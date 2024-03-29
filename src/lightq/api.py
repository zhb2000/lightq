import asyncio
import json
import urllib.parse
import typing
from collections import deque
from typing import Any, Literal, AsyncIterator, TypedDict, cast

import websockets.client
import websockets.exceptions

from . import entities
from .exceptions import MiraiApiException, TargetNotExist
from ._commons import AutoIncrement, to_camel_case
from .logging import logger
from .entities import (
    Message,
    Event,
    SyncMessage,
    UnsupportedEntity,
    MessageChain,
    Plain,
    Friend,
    Group,
    Member,
    Profile,
    GroupConfig,
    Announcement
)

__all__ = ['MiraiApi']


class DataQueue:
    def __init__(self):
        self.__queue: deque[dict[str, Any]] = deque()
        self.__consumers: deque[asyncio.Future[dict[str, Any]]] = deque()

    async def pop(self) -> dict[str, Any]:
        if len(self.__queue) > 0:
            return self.__queue.popleft()
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        self.__consumers.append(future)

        def remove_future(_):
            # the future may not be in the queue because the `clear` method may have called
            if future in self.__consumers:
                self.__consumers.remove(future)

        future.add_done_callback(remove_future)
        return await future

    def push(self, data: dict[str, Any]):
        if len(self.__consumers) > 0:
            self.__consumers[0].set_result(data)
        else:
            self.__queue.append(data)

    def set_exceptions(self, exception: BaseException):
        for future in self.__consumers:
            if not future.done():
                future.set_exception(exception)

    def clear(self):
        self.__queue.clear()
        # If the future is already done or canceled, future.cancel() will do nothing.
        for future in self.__consumers:
            future.cancel()
        self.__consumers.clear()


class ResponseDict:
    def __init__(self):
        self.__responses: dict[str, dict[str, Any]] = {}  # sync-id => response-data
        self.__consumers: dict[str, asyncio.Future[dict[str, Any]]] = {}  # sync-id => future

    async def get(self, sync_id: str) -> dict[str, Any]:
        if sync_id in self.__responses:
            return self.__responses.pop(sync_id)
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        if sync_id in self.__consumers:
            raise KeyError(f'there is already a future waiting for response with sync_id: {sync_id}')
        self.__consumers[sync_id] = future
        # the future may not be in the dict because the `clear` method may have called
        future.add_done_callback(lambda _: self.__consumers.pop(sync_id, None))
        return await future

    def put(self, sync_id: str, response: dict[str, Any]):
        if sync_id in self.__consumers:
            self.__consumers[sync_id].set_result(response)
        else:
            self.__responses[sync_id] = response

    def set_exceptions(self, exception: BaseException):
        for future in self.__consumers.values():
            if not future.done():
                future.set_exception(exception)

    def clear(self):
        self.__responses.clear()
        for future in self.__consumers.values():
            future.cancel()
        self.__consumers.clear()


class MiraiApi:
    def __init__(
        self,
        bot_id: int,
        verify_key: str,
        base_url: str = 'ws://localhost:8080',
        reserved_sync_id: str = '-1'
    ):
        self.bot_id = bot_id
        self.verify_key = verify_key
        self.base_url = base_url
        self.reserved_sync_id = reserved_sync_id
        self.__ws: websockets.client.WebSocketClientProtocol | None = None
        self.__session_key: str | None = None
        self.__queue = DataQueue()
        self.__responses = ResponseDict()
        self.__working_task: asyncio.Task[None] | None = None
        self.__increment_id = AutoIncrement(max_value=int(1e8))

    @property
    def session_key(self) -> str | None: return self.__session_key

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Mirai-api-http 传入格式：

        ```json
        {
            "syncId": 123, // 消息同步的字段
            "command": "sendFriendMessage", // 命令字
            "subCommand": null, // 子命令字, 可空
            "content": {} // 命令的数据对象, 与通用接口定义相同
        }
        ```

        JSON 的 `syncId` 字段由 `send` 方法自动生成，无需传入。

        :returns: 若状态码为 0 则将响应的 JSON 返回
        :raises:
            MiraiApiException: 若状态码非 0 则抛出对应的异常
            websockets.exception.WebSocketException: WebSocket 连接被关闭或出错时抛出
        """
        await self.connect()
        if typing.TYPE_CHECKING:
            assert self.__ws is not None
        sync_id = self.__increment_id.get()
        data['syncId'] = sync_id
        logger.info(f'websocket send: {data}')
        await self.__ws.send(json.dumps(data))
        # 响应结果的 syncId 为字符串而非数字
        response = await self.__responses.get(str(sync_id))
        response = cast(dict[str, Any], response['data'])
        if 'code' not in response:  # 有的响应不含 code 字段
            return response
        if response['code'] == 0:
            return response
        else:
            raise MiraiApiException.from_response(response)

    async def recv(self) -> Message | Event | SyncMessage | UnsupportedEntity:
        """
        Mirai-api-http 推送格式：

        ```json
        {
            "syncId": "123", // 消息同步的字段
            "data": {} // 推送消息内容, 与通用接口定义相同
        }
        ```

        本方法会返回 JSON 的 `data` 部分。

        :raises websockets.exception.WebSocketException: WebSocket 连接被关闭或出错时抛出
        """
        await self.connect()
        data = await self.__queue.pop()
        data = cast(dict[str, Any], data['data'])
        if data['type'] in entities.MESSAGE_CLASSES:
            return Message.from_json(data)
        elif data['type'] in entities.EVENT_CLASSES:
            return Event.from_json(data)
        elif data['type'] in entities.SYNC_MESSAGE_CLASSES:
            return SyncMessage.from_json(data)
        else:
            return UnsupportedEntity(data)

    async def __working_method(self):
        if typing.TYPE_CHECKING:
            assert self.__ws is not None
        try:
            while True:
                data = cast(dict[str, Any], json.loads(await self.__ws.recv()))
                logger.info(f'websocket recv: {data}')
                sync_id: str = data['syncId']
                if sync_id == '':  # first message after connected
                    self.__session_key = data['data']['session']
                elif sync_id == self.reserved_sync_id:  # 他人发送的消息（并非响应结果）
                    self.__queue.push(data)
                else:  # 响应结果
                    self.__responses.put(sync_id, data)
        except websockets.exceptions.WebSocketException as exception:
            self.__queue.set_exceptions(exception)
            self.__responses.set_exceptions(exception)
        finally:
            self.__queue.clear()
            self.__responses.clear()
            self.__session_key = None
            self.__increment_id.reset()
            ws = self.__ws
            self.__ws = None
            await ws.close()  # the close method is idempotent

    async def connect(self):
        """与 mirai-api-http 建立连接。如果连接已经建立，则什么也不做。"""
        if self.__ws is not None:
            return
        encoded_key = urllib.parse.quote_plus(self.verify_key)
        self.__ws = await websockets.client.connect(
            urllib.parse.urljoin(
                self.base_url,
                f'/all?verifyKey={encoded_key}&qq={self.bot_id}'
            )
        )

        def remove_working_task(task):
            self.__working_task = None

        self.__working_task = asyncio.create_task(self.__working_method())
        self.__working_task.add_done_callback(remove_working_task)

    async def close(self):
        """断开与 mirai-api-http 的连接。如果连接已经断开，则什么也不做。"""
        if self.__ws is None:
            return
        await self.__ws.close()
        if typing.TYPE_CHECKING:
            assert self.__working_task is not None
        await self.__working_task  # wait for the working task to finish

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __aiter__(self) -> AsyncIterator[Message | Event | SyncMessage | UnsupportedEntity]:
        async def generator():
            while True:
                try:
                    yield await self.recv()
                except websockets.exceptions.ConnectionClosedOK:
                    break

        return aiter(generator())

    async def send_command(
        self,
        command: str,
        content: dict[str, Any] | None = None,
        sub_command: str | None = None
    ) -> dict[str, Any]:
        return await self.send({
            'command': command,
            'content': content if content is not None else {},
            'subCommand': sub_command
        })

    async def message_from_id(self, message_id: int, friend_or_group_id: int) -> Message | None:
        """
        通过 message id 获取消息。若该 message id 没有被缓存或缓存失效则返回 `None`。

        :param message_id: 获取消息的 message id
        :param friend_or_group_id: 好友 QQ 号或群号
        """
        try:
            return Message.from_json((await self.send_command('messageFromId', {
                'messageId': message_id,
                'target': friend_or_group_id
            }))['data'])
        except TargetNotExist:
            return None

    async def bot_list(self) -> list[int]:
        """获取已登录的 bot 账号"""
        return (await self.send_command('botList'))['data']

    # region 获取账号信息
    async def friend_list(self) -> list[Friend]:
        """获取好友列表"""
        friends: list[dict[str, Any]] = (await self.send_command('friendList'))['data']
        return [Friend.from_json(friend) for friend in friends]

    async def group_list(self) -> list[Group]:
        """获取群列表"""
        groups: list[dict[str, Any]] = (await self.send_command('groupList'))['data']
        return [Group.from_json(group) for group in groups]

    async def member_list(self, group_id: int) -> list[Member]:
        """获取群成员列表"""
        members: list[dict[str, Any]] = (await self.send_command(
            'memberList', {'target': group_id}
        ))['data']
        return [Member.from_json(member) for member in members]

    async def bot_profile(self) -> Profile:
        """获取 bot 资料"""
        return Profile.from_json(await self.send_command('botProfile'))

    async def friend_profile(self, friend_id: int) -> Profile:
        """获取好友资料"""
        return Profile.from_json(await self.send_command('friendProfile', {'target': friend_id}))

    async def member_profile(self, group_id: int, member_id: int) -> Profile:
        """获取群成员资料"""
        return Profile.from_json(await self.send_command('memberProfile', {
            'target': group_id,
            'memberId': member_id
        }))

    async def user_profile(self, user_id: int) -> Profile:
        """获取 QQ 用户资料"""
        return Profile.from_json(await self.send_command('userProfile', {'target': user_id}))

    # endregion

    # region 消息发送与撤回
    async def send_friend_message(self, friend_id: int, message: str | MessageChain) -> int:
        """发送好友消息"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send_command('sendFriendMessage', {
            'target': friend_id,
            'messageChain': chain.to_json()
        }))['messageId']

    async def send_group_message(self, group_id: int, message: str | MessageChain) -> int:
        """发送群消息"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send_command('sendGroupMessage', {
            'target': group_id,
            'messageChain': chain.to_json()
        }))['messageId']

    async def send_temp_message(self, group_id: int, member_id: int, message: str | MessageChain) -> int:
        """发送临时会话消息"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send_command('sendTempMessage', {
            'qq': member_id,
            'group': group_id,
            'messageChain': chain.to_json()
        }))['messageId']

    async def send_nudge(
        self,
        user_id: int,
        subject: int,
        kind: Literal['Friend', 'Group', 'Stranger']
    ):
        """
        发送头像戳一戳消息

        :param user_id: 戳一戳的目标 QQ 号, 可以为 bot QQ 号
        :param subject: 戳一戳接受主体（上下文）, 戳一戳信息会发送至该主体, 为群号/好友 QQ 号
        :param kind: 上下文类型, 可选值 Friend, Group, Stranger
        """
        await self.send_command('sendNudge', {
            'target': user_id,
            'subject': subject,
            'kind': kind
        })

    async def recall(self, message_id: int, friend_or_group_id: int):
        """
        撤回消息

        :param message_id: 需要撤回的消息的 message id
        :param friend_or_group_id: 好友 QQ 号或群号
        """
        await self.send_command('recall', {
            'messageId': message_id,
            'target': friend_or_group_id
        })

    # endregion

    async def delete_friend(self, friend_id: int):
        """删除好友"""
        await self.send_command('deleteFriend', {'target': friend_id})

    # region 群管理
    async def mute(self, group_id: int, member_id: int, time: int):
        """
        禁言群成员

        :param group_id: 指定群的群号
        :param member_id: 指定群员QQ号
        :param time: 禁言时长，单位为秒，最多 30 天
        """
        await self.send_command('mute', {
            'target': group_id,
            'memberId': member_id,
            'time': time
        })

    async def unmute(self, group_id: int, member_id: int):
        """解除群成员禁言"""
        await self.send_command('unmute', {
            'target': group_id,
            'memberId': member_id
        })

    async def kick(self, group_id: int, member_id: int, message: str | None = None):
        """移除群成员"""
        await self.send_command('kick', {
            'target': group_id,
            'memberId': member_id,
            'message': message
        })

    async def quit(self, group_id: int):
        """退出群聊"""
        await self.send_command('quit', {'target': group_id})

    async def mute_all(self, group_id: int):
        """全体禁言"""
        await self.send_command('muteAll', {'target': group_id})

    async def unmute_all(self, group_id: int):
        """解除全体禁言"""
        await self.send_command('unmuteAll', {'target': group_id})

    async def set_essence(self, message_id: int, group_id: int):
        """
        设置群精华消息

        :param message_id: 精华消息的 message id
        :param group_id: 群号
        """
        await self.send_command('setEssence', {
            'messageId': message_id,
            'target': group_id
        })

    async def get_group_config(self, group_id: int) -> GroupConfig:
        """获取群设置"""
        return GroupConfig.from_json(await self.send_command(
            'groupConfig', {'target': group_id}, 'get'
        ))

    __GroupConfigDict = TypedDict('__GroupConfigDict', {
        'name': str,  # 群名称
        'announcement': str,  # 群公告
        'confess_talk': bool,
        'allow_member_invite': bool,
        'auto_approve': bool,
        'anonymous_chat': bool,
    }, total=False)

    async def update_group_config(self, group_id: int, config: __GroupConfigDict):
        """更新群设置"""
        await self.send_command('groupConfig', {
            'target': group_id,
            'config': {to_camel_case(key): value for key, value in config.items()}
        }, 'update')

    async def get_member_info(self, group_id: int, member_id: int) -> Member:
        """获取群员资料"""
        return Member.from_json(await self.send_command('memberInfo', {
            'target': group_id,
            'memberId': member_id
        }, 'get'))

    __MemberInfoDict = TypedDict('__MemberInfoDict', {
        'name': str,  # 群名片
        'special_title': str  # 群头衔
    }, total=False)

    async def update_member_info(self, group_id: int, member_id: int, info: __MemberInfoDict):
        """修改群员资料"""
        await self.send_command('memberInfo', {
            'target': group_id,
            'memberId': member_id,
            'info': {to_camel_case(key): value for key, value in info.items()}
        }, 'update')

    async def member_admin(self, group_id: int, member_id: int, assign: bool):
        """
        修改群员管理员

        :param group_id: 指定群的群号
        :param member_id: 群员 QQ 号
        :param assign: 是否设置为管理员
        """
        await self.send_command('memberAdmin', {
            'target': group_id,
            'memberId': member_id,
            'assign': assign
        })

    # endregion

    # region 群公告
    async def announcement_list(self, group_id: int, offset: int = 0, size: int = 10) -> list[Announcement]:
        """
        获取群公告列表

        :param group_id: 群号
        :param offset: 分页参数
        :param size: 分页参数，默认10
        """
        announcements: list[dict[str, Any]] = (await self.send_command('anno_list', {
            'id': group_id,
            'offset': offset,
            'size': size
        }))['data']
        return [Announcement.from_json(announcement) for announcement in announcements]

    async def publish_announcement(
        self,
        group_id: int,
        content: str,
        *,
        pinned: bool = False,
        send_to_new_member: bool = False,
        show_edit_card: bool = False,
        show_popup: bool = False,
        required_confirmation: bool = False,
        image_url: str | None = None,
        image_path: str | None = None,
        image_base64: str | None = None
    ) -> Announcement:
        """
        发布群公告

        :param group_id: 群号
        :param content: 公告内容
        :param pinned: 是否置顶
        :param send_to_new_member: 是否发送给新成员
        :param show_edit_card: 是否显示群成员修改群名片的引导
        :param show_popup: 是否自动弹出
        :param required_confirmation: 是否需要群成员确认
        :param image_url: 公告图片 url
        :param image_path: 公告图片本地路径
        :param image_base64: 公告图片 base64 编码
        """
        announcement: dict[str, Any] = (await self.send_command('anno_publish', {
            'target': group_id,
            'content': content,
            'pinned': pinned,
            'sendToNewMember': send_to_new_member,
            'showEditCard': show_edit_card,
            'showPopup': show_popup,
            'requiredConfirmation': required_confirmation,
            'imageUrl': image_url,
            'imagePath': image_path,
            'imageBase64': image_base64
        }))['data']
        return Announcement.from_json(announcement)

    async def delete_announcement(self, group_id: int, fid: str):
        """
        删除群公告

        :param group_id: 群号
        :param fid: 群公告唯一 id
        """
        await self.send_command('anno_delete', {'id': group_id, 'fid': fid})
    # endregion
