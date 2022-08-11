import abc
import importlib
from dataclasses import dataclass
from typing import Any

from . import _mixin as mixin
from ._entity import Entity
from ._element import MessageChain
from ._commons import Friend, Group, Member

__all__ = [
    'SyncMessage',
    'SYNC_MESSAGE_CLASSES',
    'FriendSyncMessage',
    'GroupSyncMessage',
    'TempSyncMessage',
    'StrangerSyncMessage'
]


class SyncMessage(Entity, mixin.FromContextData, abc.ABC):
    """
    同步消息和普通消息一样, 但是由 Bot 账号的其他客户端发送的消息, 同步到 mirai 时产生的事件。
    此类事发送人永远是 Bot 本身, 故省略。
    """
    subject: Friend | Group | Member
    message_chain: MessageChain

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> 'SyncMessage':
        return sync_message_from_json(obj)


class AbstractSyncMessage(mixin.FromJson, mixin.ToJson, SyncMessage, abc.ABC):
    pass


@dataclass
class FriendSyncMessage(AbstractSyncMessage):
    """同步好友消息"""

    subject: Friend
    """发送的目标好友"""

    message_chain: MessageChain


@dataclass
class GroupSyncMessage(AbstractSyncMessage):
    """同步群消息"""

    subject: Group
    """发送的目标群"""

    message_chain: MessageChain


@dataclass
class TempSyncMessage(AbstractSyncMessage):
    """同步群临时消息"""

    subject: Member
    """发送的目标群成员，对应群信息在群成员的 group 字段"""

    message_chain: MessageChain


@dataclass
class StrangerSyncMessage(AbstractSyncMessage):
    """同步陌生人消息"""

    subject: Friend
    """发送的目标陌生人账号"""

    message_chain: MessageChain


def make_sync_message_class_dict() -> dict[str, type[SyncMessage]]:
    module = importlib.import_module(__name__)
    exclude = ('SyncMessage', 'SYNC_MESSAGE_CLASSES')
    return {name: getattr(module, name) for name in __all__ if name not in exclude}


SYNC_MESSAGE_CLASSES = make_sync_message_class_dict()


def sync_message_from_json(obj: dict[str, Any]) -> SyncMessage:
    cls = SYNC_MESSAGE_CLASSES[obj['type']]
    return cls.from_json(obj)
