import abc
import importlib
from dataclasses import dataclass
from typing import Any

from . import _mixin as mixin
from ._commons import Friend, Group, Member, Client
from ._element import MessageChain
from ._entity import Entity

__all__ = [
    'Event',
    'EVENT_CLASSES',
    'BotOnlineEvent',
    'BotOfflineEventActive',
    'BotOfflineEventForce',
    'BotOfflineEventDropped',
    'BotReloginEvent',
    'FriendInputStatusChangedEvent',
    'FriendNickChangedEvent',
    'BotGroupPermissionChangeEvent',
    'BotMuteEvent',
    'BotUnmuteEvent',
    'BotJoinGroupEvent',
    'BotLeaveEventActive',
    'BotLeaveEventKick',
    'BotLeaveEventDisband',
    'GroupRecallEvent',
    'FriendRecallEvent',
    'NudgeEvent',
    'GroupNameChangeEvent',
    'GroupEntranceAnnouncementChangeEvent',
    'GroupMuteAllEvent',
    'GroupAllowAnonymousChatEvent',
    'GroupAllowConfessTalkEvent',
    'GroupAllowMemberInviteEvent',
    'MemberJoinEvent',
    'MemberLeaveEventKick',
    'MemberLeaveEventQuit',
    'MemberCardChangeEvent',
    'MemberSpecialTitleChangeEvent',
    'MemberPermissionChangeEvent',
    'MemberMuteEvent',
    'MemberUnmuteEvent',
    'MemberHonorChangeEvent',
    'NewFriendRequestEvent',
    'MemberJoinRequestEvent',
    'BotInvitedJoinGroupRequestEvent',
    'OtherClientOnlineEvent',
    'OtherClientOfflineEvent',
    'CommandExecutedEvent'
]


class Event(Entity, mixin.FromContextData, abc.ABC):
    @abc.abstractclassmethod
    def to_json(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> 'Event':
        return event_from_json(obj)


class AbstractEvent(mixin.FromJson, mixin.ToJson, Event, abc.ABC):
    pass


# region Bot 自身事件

@dataclass
class BotOnlineEvent(AbstractEvent):
    """Bot 登录成功"""

    qq: int
    """登录成功的 Bot 的 QQ 号"""


@dataclass
class BotOfflineEventActive(AbstractEvent):
    """Bot 主动离线"""

    qq: int
    """主动离线的 Bot 的 QQ 号"""


@dataclass
class BotOfflineEventForce(AbstractEvent):
    """Bot 被挤下线"""

    qq: int
    """被挤下线的 Bot 的 QQ 号"""


@dataclass
class BotOfflineEventDropped(AbstractEvent):
    """Bot 被服务器断开或因网络问题而掉线"""

    qq: int
    """被服务器断开或因网络问题而掉线的 Bot 的 QQ 号"""


@dataclass
class BotReloginEvent(AbstractEvent):
    """Bot 主动重新登录"""

    qq: int
    """主动重新登录的 Bot 的 QQ 号"""


# endregion Bot 自身事件

# region 好友事件

@dataclass
class FriendInputStatusChangedEvent(AbstractEvent):
    """好友输入状态改变"""

    friend: Friend

    inputting: bool
    """当前输出状态是否正在输入"""


@dataclass
class FriendNickChangedEvent(AbstractEvent):
    """好友昵称改变"""

    friend: Friend

    from_: str
    """原昵称"""

    to: str
    """新昵称"""


# endregion 好友事件

# region 群事件

@dataclass
class BotGroupPermissionChangeEvent(AbstractEvent):
    """Bot 在群里的权限被改变，操作人一定是群主"""

    origin: str
    """Bot 的原权限，OWNER、ADMINISTRATOR 或 MEMBER"""

    current: str
    """Bot 的新权限，OWNER、ADMINISTRATOR 或 MEMBER"""

    group: Group


@dataclass
class BotMuteEvent(AbstractEvent):
    """Bot 被禁言"""

    duration_seconds: int
    """禁言时长，单位为秒"""

    operator: Member
    """操作的管理员或群主信息"""


@dataclass
class BotUnmuteEvent(AbstractEvent):
    """Bot 被取消禁言"""

    operator: Member
    """操作的管理员或群主信息"""


@dataclass
class BotJoinGroupEvent(AbstractEvent):
    """Bot 加入了一个新群"""

    group: Group
    """Bot 新加入群的信息"""

    invitor: Member | None
    """如果被要求入群的话，则为邀请人的 Member 对象"""


@dataclass
class BotLeaveEventActive(AbstractEvent):
    """Bot 主动退出一个群"""

    group: Group
    """Bot 退出的群的信息"""


@dataclass
class BotLeaveEventKick(AbstractEvent):
    """Bot 被踢出一个群"""

    group: Group
    """Bot 被踢出的群的信息"""

    operator: Member | None
    """Bot 被踢后获取操作人的 Member 对象"""


@dataclass
class BotLeaveEventDisband(AbstractEvent):
    """Bot 因群主解散群而退出群, 操作人一定是群主"""

    group: Group
    """Bot 所在被解散的群的信息"""

    operator: Member | None
    """Bot 离开群后获取操作人的 Member 对象"""


@dataclass
class GroupRecallEvent(AbstractEvent):
    """群消息撤回"""

    author_id: int
    """原消息发送者的 QQ 号"""

    message_id: int
    """原消息 messageId"""

    time: int
    """原消息发送时间"""

    group: Group
    """消息撤回所在的群"""

    operator: Member | None
    """撤回消息的操作人，当 null 时为 bot 操作"""


@dataclass
class FriendRecallEvent(AbstractEvent):
    """好友消息撤回"""

    author_id: int
    """原消息发送者的 QQ 号"""

    message_id: int
    """原消息 messageId"""

    time: int
    """原消息发送时间"""

    operator: int
    """好友 QQ 号或 Bot QQ 号"""


@dataclass
class NudgeEvent(AbstractEvent):
    """戳一戳事件"""

    @dataclass
    class Subject(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
        id: int
        """来源的 QQ 号（好友）或群号"""

        kind: str
        """来源的类型，Friend 或 Group"""

    from_id: int
    """动作发出者的 QQ 号"""

    subject: Subject
    """来源"""

    action: str
    """动作类型"""

    suffix: str
    """自定义动作内容"""

    target: int
    """动作目标的QQ号"""


@dataclass
class GroupNameChangeEvent(AbstractEvent):
    """某个群名改变"""

    origin: str
    """原群名"""

    current: str
    """新群名"""

    group: Group
    """群名改名的群信息"""

    operator: Member | None
    """操作的管理员或群主信息，当 null 时为 Bot 操作"""


@dataclass
class GroupEntranceAnnouncementChangeEvent(AbstractEvent):
    """某群入群公告改变"""

    origin: str
    """原公告"""

    current: str
    """新公告"""

    group: Group
    """公告改变的群信息"""

    operator: Member | None
    """操作的管理员或群主信息，当 null 时为 Bot 操作"""


@dataclass
class GroupMuteAllEvent(AbstractEvent):
    """全员禁言"""

    origin: bool
    """原本是否处于全员禁言"""

    current: bool
    """现在是否处于全员禁言"""

    group: Group
    """全员禁言的群信息"""

    operator: Member | None
    """操作的管理员或群主信息，当 null 时为 Bot 操作"""


@dataclass
class GroupAllowAnonymousChatEvent(AbstractEvent):
    """匿名聊天"""

    origin: bool
    """原本匿名聊天是否开启"""

    current: bool
    """现在匿名聊天是否开启"""

    group: Group
    """匿名聊天状态改变的群信息"""

    operator: Member | None
    """操作的管理员或群主信息，当 null 时为 Bot 操作"""


@dataclass
class GroupAllowConfessTalkEvent(AbstractEvent):
    """坦白说"""

    origin: bool
    """原本坦白说是否开启"""

    current: bool
    """现在坦白说是否开启"""

    group: Group
    """坦白说状态改变的群信息"""

    is_by_bot: bool
    """是否Bot进行该操作"""


@dataclass
class GroupAllowMemberInviteEvent(AbstractEvent):
    """允许群员邀请好友加群"""

    origin: bool
    """原本是否允许群员邀请好友加群"""

    current: bool
    """现在是否允许群员邀请好友加群"""

    group: Group
    """允许群员邀请好友加群状态改变的群信息"""

    operator: Member | None
    """操作的管理员或群主信息，当 null 时为 Bot 操作"""


@dataclass
class MemberJoinEvent(AbstractEvent):
    """新人入群的事件"""

    member: Member
    """新人信息"""

    invitor: Member | None
    """如果被要求入群的话，则为邀请人的 Member 对象"""


@dataclass
class MemberLeaveEventKick(AbstractEvent):
    """成员被踢出群（该成员不是 bot）"""

    member: Member
    """被踢者的信息"""

    operator: Member | None
    """操作的管理员或群主信息，当 null 时为 Bot 操作"""


@dataclass
class MemberLeaveEventQuit(AbstractEvent):
    """成员主动离群（该成员不是 bot）"""

    member: Member
    """退群群员的信息"""


@dataclass
class MemberCardChangeEvent(AbstractEvent):
    """群名片改动"""

    origin: str
    """原本名片"""

    current: str
    """现在名片"""

    member: Member
    """名片改动的群员的信息"""


@dataclass
class MemberSpecialTitleChangeEvent(AbstractEvent):
    """群头衔改动（只有群主有操作限权）"""

    origin: str
    """原头衔"""

    current: str
    """现头衔"""

    member: Member
    """头衔改动的群员的信息"""


@dataclass
class MemberPermissionChangeEvent(AbstractEvent):
    """成员权限改变的事件（该成员不是 bot）"""

    origin: str
    """原权限"""

    current: str
    """现权限"""

    member: Member
    """权限改动的群员的信息"""


@dataclass
class MemberMuteEvent(AbstractEvent):
    """群成员被禁言事件（该成员不是 bot）"""

    duration_seconds: int
    """禁言时长，单位为秒"""

    member: Member
    """被禁言的群员的信息"""

    operator: Member | None
    """操作者的信息，当 null 时为 Bot 操作"""


@dataclass
class MemberUnmuteEvent(AbstractEvent):
    """群成员被取消禁言事件（该成员不是 bot）"""

    member: Member
    """被取消禁言的群员的信息"""

    operator: Member | None
    """操作者的信息，当 null 时为 Bot 操作"""


@dataclass
class MemberHonorChangeEvent(AbstractEvent):
    """群员称号改变"""

    member: Member
    """称号改变的群员的信息"""

    action: str
    """称号变化行为：achieve 获得称号，lose 失去称号"""

    honor: str
    """称号名称"""


# endregion 群事件

# region 申请事件

@dataclass
class NewFriendRequestEvent(AbstractEvent):
    """添加好友申请"""

    event_id: int
    """事件标识，响应该事件时的标识"""

    from_id: int
    """申请人QQ号"""

    group_id: int
    """申请人如果通过某个群添加好友，该项为该群群号，否则为 0"""

    nick: str
    """申请人的昵称或群名片"""

    message: str
    """申请消息"""


@dataclass
class MemberJoinRequestEvent(AbstractEvent):
    """用户入群申请（bot 需要有管理员权限）"""

    event_id: int
    """事件标识，响应该事件时的标识"""

    from_id: int
    """申请人 QQ 号"""

    group_id: int
    """申请人申请入群的群号"""

    group_name: str
    """申请人申请入群的群名称"""

    nick: str
    """申请人的昵称或群名片"""

    message: str
    """申请消息"""


@dataclass
class BotInvitedJoinGroupRequestEvent(AbstractEvent):
    """Bot 被邀请入群申请"""

    event_id: int
    """事件标识，响应该事件时的标识"""

    from_id: int
    """邀请人（好友）的QQ号"""

    group_id: int
    """被邀请进入群的群号"""

    group_name: str
    """被邀请进入群的群名称"""

    nick: str
    """邀请人（好友）的昵称"""

    message: str
    """邀请消息"""


# endregion 申请事件

# region 其他客户端事件

@dataclass
class OtherClientOnlineEvent(AbstractEvent):
    """其他客户端上线"""

    client: Client
    """其他客户端"""

    kind: int | None
    """详细设备类型"""


@dataclass
class OtherClientOfflineEvent(AbstractEvent):
    """其他客户端下线"""

    client: Client
    """其他客户端"""


# endregion 其他客户端事件

# region 命令事件

@dataclass
class CommandExecutedEvent(AbstractEvent):
    """命令被执行"""

    name: str
    """命令名称"""

    friend: Friend | None
    """发送命令的好友, 从控制台发送为 null"""

    member: Member | None
    """发送命令的群成员, 从控制台发送为 null"""

    args: MessageChain
    """指令的参数, 以消息类型传递"""


# endregion 命令事件


def make_event_class_dict() -> dict[str, type[Event]]:
    module = importlib.import_module(__name__)
    exclude = ('Event', 'EVENT_CLASSES')
    return {name: getattr(module, name) for name in __all__ if name not in exclude}


EVENT_CLASSES = make_event_class_dict()


def event_from_json(obj: dict[str, Any]) -> Event:
    cls = EVENT_CLASSES[obj['type']]
    return cls.from_json(obj)
