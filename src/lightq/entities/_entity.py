import abc
from typing import Any, TypeVar

Self = TypeVar('Self')


class Entity(abc.ABC):
    @abc.abstractmethod
    def to_json(self) -> dict[str, Any] | list[dict[str, Any]]:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def from_json(cls: type[Self], obj: dict[str, Any] | list[dict[str, Any]]) -> Self:
        raise NotImplementedError(
            'Use the following method instead: '
            'Message.from_json, Event.from_json, SyncMessage.from_json, '
            'MessageElement.from_json, MessageChain.from_json'
        )


class UnsupportedEntity(Entity):
    def __init__(self, data: dict[str, Any]):
        self.data = data

    def to_json(self) -> dict[str, Any]:
        return self.data

    @classmethod
    def from_json(cls: type[Self], obj: dict[str, Any]) -> Self:
        return cls(obj)
