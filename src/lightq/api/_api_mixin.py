from abc import abstractmethod
from typing import Any, Literal, TypedDict

from .._commons import to_camel_case
from ..exceptions import TargetNotExist
from ..entities import (
    Message,
    MessageChain,
    Plain,
    Friend,
    Group,
    Member,
    Profile,
    GroupConfig,
    Announcement
)


class GroupConfigDict(TypedDict, total=False):
    name: str
    announcement: str
    """群公告"""

    confess_talk: bool
    allow_member_invite: bool
    auto_approve: bool
    anonymous_chat: bool


class MemberInfoDict(TypedDict, total=False):
    name: str
    """群名片"""

    special_title: str
    """群头衔"""


class ApiMixin:
    @abstractmethod
    async def __send_command__(
        self,
        command: str,
        content: dict[str, Any] | None = None,
        sub_command: str | None = None
    ):
        raise NotImplementedError

    async def message_from_id(self, message_id: int, friend_or_group_id: int) -> Message | None:
        """
        通过 message id 获取消息。若该 message id 没有被缓存或缓存失效则返回 `None`。

        :param message_id: 获取消息的 message id
        :param friend_or_group_id: 好友 QQ 号或群号
        """
        try:
            return Message.from_json((await self.__send_command__('messageFromId', {
                'messageId': message_id,
                'target': friend_or_group_id
            }))['data'])
        except TargetNotExist:
            return None

    async def bot_list(self) -> list[int]:
        """获取已登录的 bot 账号"""
        return (await self.__send_command__('botList'))['data']

    # region 获取账号信息
    async def friend_list(self) -> list[Friend]:
        """获取好友列表"""
        friends: list[dict[str, Any]] = (await self.__send_command__('friendList'))['data']
        return [Friend.from_json(friend) for friend in friends]

    async def group_list(self) -> list[Group]:
        """获取群列表"""
        groups: list[dict[str, Any]] = (await self.__send_command__('groupList'))['data']
        return [Group.from_json(group) for group in groups]

    async def member_list(self, group_id: int) -> list[Member]:
        """获取群成员列表"""
        members: list[dict[str, Any]] = (await self.__send_command__(
            'memberList', {'target': group_id}
        ))['data']
        return [Member.from_json(member) for member in members]

    async def bot_profile(self) -> Profile:
        """获取 bot 资料"""
        return Profile.from_json(await self.__send_command__('botProfile'))

    async def friend_profile(self, friend_id: int) -> Profile:
        """获取好友资料"""
        return Profile.from_json(await self.__send_command__('friendProfile', {'target': friend_id}))

    async def member_profile(self, group_id: int, member_id: int) -> Profile:
        """获取群成员资料"""
        return Profile.from_json(await self.__send_command__('memberProfile', {
            'target': group_id,
            'memberId': member_id
        }))

    async def user_profile(self, user_id: int) -> Profile:
        """获取 QQ 用户资料"""
        return Profile.from_json(await self.__send_command__('userProfile', {'target': user_id}))
    # endregion

    # region 消息发送与撤回
    async def send_friend_message(self, friend_id: int, message: str | MessageChain) -> int:
        """发送好友消息"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.__send_command__('sendFriendMessage', {
            'target': friend_id,
            'messageChain': chain.to_json()
        }))['messageId']

    async def send_group_message(self, group_id: int, message: str | MessageChain) -> int:
        """发送群消息"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.__send_command__('sendGroupMessage', {
            'target': group_id,
            'messageChain': chain.to_json()
        }))['messageId']

    async def send_temp_message(self, group_id: int, member_id: int, message: str | MessageChain) -> int:
        """发送临时会话消息"""
        chain = MessageChain([Plain(message)]) if isinstance(message, str) else message
        return (await self.__send_command__('sendTempMessage', {
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
        await self.__send_command__('sendNudge', {
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
        await self.__send_command__('recall', {
            'messageId': message_id,
            'target': friend_or_group_id
        })
    # endregion

    async def delete_friend(self, friend_id: int):
        """删除好友"""
        await self.__send_command__('deleteFriend', {'target': friend_id})

    # region 群管理
    async def mute(self, group_id: int, member_id: int, time: int):
        """
        禁言群成员

        :param group_id: 指定群的群号
        :param member_id: 指定群员QQ号
        :param time: 禁言时长，单位为秒，最多 30 天
        """
        await self.__send_command__('mute', {
            'target': group_id,
            'memberId': member_id,
            'time': time
        })

    async def unmute(self, group_id: int, member_id: int):
        """解除群成员禁言"""
        await self.__send_command__('unmute', {
            'target': group_id,
            'memberId': member_id
        })

    async def kick(self, group_id: int, member_id: int, message: str | None = None):
        """移除群成员"""
        await self.__send_command__('kick', {
            'target': group_id,
            'memberId': member_id,
            'message': message
        })

    async def quit(self, group_id: int):
        """退出群聊"""
        await self.__send_command__('quit', {'target': group_id})

    async def mute_all(self, group_id: int):
        """全体禁言"""
        await self.__send_command__('muteAll', {'target': group_id})

    async def unmute_all(self, group_id: int):
        """解除全体禁言"""
        await self.__send_command__('unmuteAll', {'target': group_id})

    async def set_essence(self, message_id: int, group_id: int):
        """
        设置群精华消息

        :param message_id: 精华消息的 message id
        :param group_id: 群号
        """
        await self.__send_command__('setEssence', {
            'messageId': message_id,
            'target': group_id
        })

    async def get_group_config(self, group_id: int) -> GroupConfig:
        """获取群设置"""
        return GroupConfig.from_json(await self.__send_command__(
            'groupConfig', {'target': group_id}, 'get'
        ))

    async def update_group_config(self, group_id: int, config: GroupConfigDict):
        """更新群设置"""
        await self.__send_command__('groupConfig', {
            'target': group_id,
            'config': {to_camel_case(key): value for key, value in config.items()}
        }, 'update')

    async def get_member_info(self, group_id: int, member_id: int) -> Member:
        """获取群员资料"""
        return Member.from_json(await self.__send_command__('memberInfo', {
            'target': group_id,
            'memberId': member_id
        }, 'get'))

    async def update_member_info(self, group_id: int, member_id: int, info: MemberInfoDict):
        """修改群员资料"""
        await self.__send_command__('memberInfo', {
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
        await self.__send_command__('memberAdmin', {
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
        announcements: list[dict[str, Any]] = (await self.__send_command__('anno_list', {
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
        announcement: dict[str, Any] = (await self.__send_command__('anno_publish', {
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
        await self.__send_command__('anno_delete', {'id': group_id, 'fid': fid})
    # endregion
