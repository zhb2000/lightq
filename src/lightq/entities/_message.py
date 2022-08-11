import abc
import importlib
from typing import Any
from dataclasses import dataclass

from . import _mixin as mixin
from ._commons import Friend, Member, Client
from ._element import MessageChain
from ._entity import Entity

__all__ = [
    'Message',
    'MESSAGE_CLASSES',
    'FriendMessage',
    'GroupMessage',
    'TempMessage',
    'StrangerMessage',
    'OtherClientMessage'
]


class Message(Entity, mixin.FromContextData, abc.ABC):
    sender: Friend | Member | Client
    message_chain: MessageChain

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> 'Message':
        return message_from_json(obj)


class AbstractMessage(mixin.FromJson, mixin.ToJson, Message, abc.ABC):
    pass


@dataclass
class FriendMessage(AbstractMessage):
    """好友消息"""
    sender: Friend
    message_chain: MessageChain


@dataclass
class GroupMessage(AbstractMessage):
    """群消息"""
    sender: Member
    message_chain: MessageChain


@dataclass
class TempMessage(AbstractMessage):
    """群临时消息"""
    sender: Member
    message_chain: MessageChain


@dataclass
class StrangerMessage(AbstractMessage):
    """陌生人消息"""
    sender: Friend
    message_chain: MessageChain


@dataclass
class OtherClientMessage(AbstractMessage):
    """其他客户端消息"""
    sender: Client
    message_chain: MessageChain


def make_message_class_dict() -> dict[str, type[Message]]:
    module = importlib.import_module(__name__)
    exclude = ('Message', 'MESSAGE_CLASSES')
    return {name: getattr(module, name) for name in __all__ if name not in exclude}


MESSAGE_CLASSES = make_message_class_dict()


def message_from_json(obj: dict[str, Any]) -> Message:
    cls = MESSAGE_CLASSES[obj['type']]
    return cls.from_json(obj)
