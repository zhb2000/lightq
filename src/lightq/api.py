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
        Mirai-api-http ???????????????

        ```json
        {
            "syncId": 123, // ?????????????????????
            "command": "sendFriendMessage", // ?????????
            "subCommand": null, // ????????????, ??????
            "content": {} // ?????????????????????, ???????????????????????????
        }
        ```

        JSON ??? `syncId` ????????? `send` ????????????????????????????????????

        :returns: ??????????????? 0 ??????????????? JSON ??????
        :raises:
            MiraiApiException: ??????????????? 0 ????????????????????????
            websockets.exception.WebSocketException: WebSocket ?????????????????????????????????
        """
        await self.connect()
        if typing.TYPE_CHECKING:
            assert self.__ws is not None
        sync_id = self.__increment_id.get()
        data['syncId'] = sync_id
        logger.info(f'websocket send: {data}')
        await self.__ws.send(json.dumps(data))
        # ??????????????? syncId ????????????????????????
        response = await self.__responses.get(str(sync_id))
        response = cast(dict[str, Any], response['data'])
        if 'code' not in response:  # ?????????????????? code ??????
            return response
        if response['code'] == 0:
            return response
        else:
            raise MiraiApiException.from_response(response)

    async def recv(self) -> Message | Event | SyncMessage | UnsupportedEntity:
        """
        Mirai-api-http ???????????????

        ```json
        {
            "syncId": "123", // ?????????????????????
            "data": {} // ??????????????????, ???????????????????????????
        }
        ```

        ?????????????????? JSON ??? `data` ?????????

        :raises websockets.exception.WebSocketException: WebSocket ?????????????????????????????????
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
                elif sync_id == self.reserved_sync_id:  # ?????????????????????????????????????????????
                    self.__queue.push(data)
                else:  # ????????????
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
        """??? mirai-api-http ???????????????????????????????????????????????????????????????"""
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
        """????????? mirai-api-http ????????????????????????????????????????????????????????????"""
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
        ?????? message id ????????????????????? message id ??????????????????????????????????????? `None`???

        :param message_id: ??????????????? message id
        :param friend_or_group_id: ?????? QQ ????????????
        """
        try:
            return Message.from_json((await self.send_command('messageFromId', {
                'messageId': message_id,
                'target': friend_or_group_id
            }))['data'])
        except TargetNotExist:
            return None

    async def bot_list(self) -> list[int]:
        """?????????????????? bot ??????"""
        return (await self.send_command('botList'))['data']

    # region ??????????????????
    async def friend_list(self) -> list[Friend]:
        """??????????????????"""
        friends: list[dict[str, Any]] = (await self.send_command('friendList'))['data']
        return [Friend.from_json(friend) for friend in friends]

    async def group_list(self) -> list[Group]:
        """???????????????"""
        groups: list[dict[str, Any]] = (await self.send_command('groupList'))['data']
        return [Group.from_json(group) for group in groups]

    async def member_list(self, group_id: int) -> list[Member]:
        """?????????????????????"""
        members: list[dict[str, Any]] = (await self.send_command(
            'memberList', {'target': group_id}
        ))['data']
        return [Member.from_json(member) for member in members]

    async def bot_profile(self) -> Profile:
        """?????? bot ??????"""
        return Profile.from_json(await self.send_command('botProfile'))

    async def friend_profile(self, friend_id: int) -> Profile:
        """??????????????????"""
        return Profile.from_json(await self.send_command('friendProfile', {'target': friend_id}))

    async def member_profile(self, group_id: int, member_id: int) -> Profile:
        """?????????????????????"""
        return Profile.from_json(await self.send_command('memberProfile', {
            'target': group_id,
            'memberId': member_id
        }))

    async def user_profile(self, user_id: int) -> Profile:
        """?????? QQ ????????????"""
        return Profile.from_json(await self.send_command('userProfile', {'target': user_id}))

    # endregion

    # region ?????????????????????
    async def send_friend_message(self, friend_id: int, message: str | MessageChain) -> int:
        """??????????????????"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send_command('sendFriendMessage', {
            'target': friend_id,
            'messageChain': chain.to_json()
        }))['messageId']

    async def send_group_message(self, group_id: int, message: str | MessageChain) -> int:
        """???????????????"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.send_command('sendGroupMessage', {
            'target': group_id,
            'messageChain': chain.to_json()
        }))['messageId']

    async def send_temp_message(self, group_id: int, member_id: int, message: str | MessageChain) -> int:
        """????????????????????????"""
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
        ???????????????????????????

        :param user_id: ?????????????????? QQ ???, ????????? bot QQ ???
        :param subject: ????????????????????????????????????, ????????????????????????????????????, ?????????/?????? QQ ???
        :param kind: ???????????????, ????????? Friend, Group, Stranger
        """
        await self.send_command('sendNudge', {
            'target': user_id,
            'subject': subject,
            'kind': kind
        })

    async def recall(self, message_id: int, friend_or_group_id: int):
        """
        ????????????

        :param message_id: ???????????????????????? message id
        :param friend_or_group_id: ?????? QQ ????????????
        """
        await self.send_command('recall', {
            'messageId': message_id,
            'target': friend_or_group_id
        })

    # endregion

    async def delete_friend(self, friend_id: int):
        """????????????"""
        await self.send_command('deleteFriend', {'target': friend_id})

    # region ?????????
    async def mute(self, group_id: int, member_id: int, time: int):
        """
        ???????????????

        :param group_id: ??????????????????
        :param member_id: ????????????QQ???
        :param time: ???????????????????????????????????? 30 ???
        """
        await self.send_command('mute', {
            'target': group_id,
            'memberId': member_id,
            'time': time
        })

    async def unmute(self, group_id: int, member_id: int):
        """?????????????????????"""
        await self.send_command('unmute', {
            'target': group_id,
            'memberId': member_id
        })

    async def kick(self, group_id: int, member_id: int, message: str | None = None):
        """???????????????"""
        await self.send_command('kick', {
            'target': group_id,
            'memberId': member_id,
            'message': message
        })

    async def quit(self, group_id: int):
        """????????????"""
        await self.send_command('quit', {'target': group_id})

    async def mute_all(self, group_id: int):
        """????????????"""
        await self.send_command('muteAll', {'target': group_id})

    async def unmute_all(self, group_id: int):
        """??????????????????"""
        await self.send_command('unmuteAll', {'target': group_id})

    async def set_essence(self, message_id: int, group_id: int):
        """
        ?????????????????????

        :param message_id: ??????????????? message id
        :param group_id: ??????
        """
        await self.send_command('setEssence', {
            'messageId': message_id,
            'target': group_id
        })

    async def get_group_config(self, group_id: int) -> GroupConfig:
        """???????????????"""
        return GroupConfig.from_json(await self.send_command(
            'groupConfig', {'target': group_id}, 'get'
        ))

    __GroupConfigDict = TypedDict('__GroupConfigDict', {
        'name': str,  # ?????????
        'announcement': str,  # ?????????
        'confess_talk': bool,
        'allow_member_invite': bool,
        'auto_approve': bool,
        'anonymous_chat': bool,
    }, total=False)

    async def update_group_config(self, group_id: int, config: __GroupConfigDict):
        """???????????????"""
        await self.send_command('groupConfig', {
            'target': group_id,
            'config': {to_camel_case(key): value for key, value in config.items()}
        }, 'update')

    async def get_member_info(self, group_id: int, member_id: int) -> Member:
        """??????????????????"""
        return Member.from_json(await self.send_command('memberInfo', {
            'target': group_id,
            'memberId': member_id
        }, 'get'))

    __MemberInfoDict = TypedDict('__MemberInfoDict', {
        'name': str,  # ?????????
        'special_title': str  # ?????????
    }, total=False)

    async def update_member_info(self, group_id: int, member_id: int, info: __MemberInfoDict):
        """??????????????????"""
        await self.send_command('memberInfo', {
            'target': group_id,
            'memberId': member_id,
            'info': {to_camel_case(key): value for key, value in info.items()}
        }, 'update')

    async def member_admin(self, group_id: int, member_id: int, assign: bool):
        """
        ?????????????????????

        :param group_id: ??????????????????
        :param member_id: ?????? QQ ???
        :param assign: ????????????????????????
        """
        await self.send_command('memberAdmin', {
            'target': group_id,
            'memberId': member_id,
            'assign': assign
        })

    # endregion

    # region ?????????
    async def announcement_list(self, group_id: int, offset: int = 0, size: int = 10) -> list[Announcement]:
        """
        ?????????????????????

        :param group_id: ??????
        :param offset: ????????????
        :param size: ?????????????????????10
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
        ???????????????

        :param group_id: ??????
        :param content: ????????????
        :param pinned: ????????????
        :param send_to_new_member: ????????????????????????
        :param show_edit_card: ?????????????????????????????????????????????
        :param show_popup: ??????????????????
        :param required_confirmation: ???????????????????????????
        :param image_url: ???????????? url
        :param image_path: ????????????????????????
        :param image_base64: ???????????? base64 ??????
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
        ???????????????

        :param group_id: ??????
        :param fid: ??????????????? id
        """
        await self.send_command('anno_delete', {'id': group_id, 'fid': fid})
    # endregion
