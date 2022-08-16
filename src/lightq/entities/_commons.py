from dataclasses import dataclass

from . import _mixin as mixin
from ._entity import Entity

__all__ = ['Friend', 'Group', 'Member', 'Client', 'Profile', 'GroupConfig', 'Announcement']


@dataclass
class Friend(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
    id: int
    """好友 QQ 号码"""

    nickname: str
    """好友昵称"""

    remark: str
    """好友备注"""


@dataclass
class Group(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
    id: int
    """群号"""

    name: str
    """群名"""

    permission: str
    """Bot在群中的权限，OWNER、ADMINISTRATOR 或 MEMBER"""


@dataclass
class Member(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
    id: int
    """QQ 号"""

    member_name: str
    """群名片"""

    permission: str
    """在群中的权限，OWNER、ADMINISTRATOR 或 MEMBER"""

    special_title: str
    """群头衔"""

    join_timestamp: int

    last_speak_timestamp: int

    mute_time_remaining: int

    group: Group


@dataclass
class Client(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
    id: int
    """客户端标识号"""

    platform: str
    """客户端类型"""


@dataclass
class Profile(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
    """用户资料"""

    nickname: str
    email: str
    age: int
    level: int
    sign: str
    sex: str
    """UNKNOWN, MALE, FEMALE"""


@dataclass
class GroupConfig(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
    """群设置"""

    name: str
    """群名称"""

    announcement: str
    """群公告"""

    confess_talk: bool
    allow_member_invite: bool
    auto_approve: bool
    anonymous_chat: bool


@dataclass
class Announcement(mixin.FromJsonWithoutType, mixin.ToJsonWithoutType, Entity):
    """群公告"""

    group: Group

    content: str
    """群公告内容"""

    sender_id: int
    """发布者账号"""

    fid: str
    """公告唯一 id"""

    all_confirmed: bool
    """是否所有群成员已确认"""

    confirmed_members_count: int
    """确认群成员人数"""

    publication_time: int
    """发布时间"""
