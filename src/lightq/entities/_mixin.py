import dataclasses
import types
import typing
import abc
from typing import Any, TypeVar

from ._entity import Entity
from .._commons import to_camel_case, is_class_annotation
from .._from_context import FromContext

if typing.TYPE_CHECKING:
    from ..framework import RecvContext

Self = TypeVar('Self')


# region to_json

class ToJson(abc.ABC):
    def to_json(self) -> dict[str, Any]:
        return {'type': type(self).__name__, **to_json(self)}


class ToJsonWithoutType(abc.ABC):
    def to_json(self) -> dict[str, Any]:
        return to_json(self)


def to_json(obj: Any) -> dict[str, Any]:
    """
    Convert a dataclass entity to JSON. Notice that ``MessageChain`` is not a dataclass.
    """
    assert dataclasses.is_dataclass(obj), 'obj is not a dataclass object'
    result = {}
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        name = to_camel_case(field.name)
        if isinstance(value, Entity):
            result[name] = value.to_json()
        elif isinstance(value, list):
            result[name] = [x.to_json() if isinstance(x, Entity) else x for x in value]
        else:
            assert isinstance(value, int | str | bool | types.NoneType)
            result[name] = value
    return result


# endregion to_json

# region from_json

class FromJson(abc.ABC):
    @classmethod
    def from_json(cls: type[Self], obj: dict[str, Any]) -> Self:
        assert obj['type'] == cls.__name__, f'Expect {cls.__name__} but the "type" in JSON is {obj["type"]}'
        return from_json(cls, obj)


class FromJsonWithoutType(abc.ABC):
    @classmethod
    def from_json(cls: type[Self], obj: dict[str, Any]) -> Self:
        return from_json(cls, obj)


def from_json(cls: type[Self], obj: dict[str, Any]) -> Self:
    return cls(**{field.name: deserialize(field.type, obj.get(to_camel_case(field.name)))
                  for field in dataclasses.fields(cls)})


def deserialize(
    annotation: Any,
    json_element: dict[str, Any] | list | int | str | bool | None
) -> Entity | list | int | str | bool | None:
    if typing.get_origin(annotation) == list:  # list[T] or List[T]
        value_type = typing.get_args(annotation)[0]  # T
        return [deserialize(value_type, x) for x in json_element]
    elif (isinstance(annotation, types.UnionType)
          or typing.get_origin(annotation) == typing.Union):  # X | Y or Union[X, Y]
        union_types = typing.get_args(annotation)  # (X, Y)
        return deserialize_union(union_types, json_element)
    elif is_class_annotation(annotation) and issubclass(annotation, Entity):
        return annotation.from_json(json_element)
    else:
        assert issubclass(annotation, int | str | bool | types.NoneType)
        return json_element


def deserialize_union(
    union_types: tuple,
    json_element: dict[str, Any] | list | int | str | bool | None
) -> Entity | list | int | str | bool | None:
    def can_deserialize(
        expected_type: type[Entity] | type[list] | type[int] | type[str] | type[bool] | type[types.NoneType]
    ) -> bool:
        if is_class_annotation(expected_type) and issubclass(expected_type, Entity):
            return isinstance(json_element, dict) or isinstance(json_element, list)
        else:  # list, int, str, bool, NoneType
            return expected_type == type(json_element)

    return next((deserialize(annotation, json_element)
                 for annotation in union_types if can_deserialize(annotation)), None)


# endregion from_json

# region from_recv_context, from_exception_context

class FromContextData(FromContext, abc.ABC):
    @classmethod
    def from_recv_context(cls: type[Self], context: 'RecvContext') -> Self:
        assert isinstance(context.data, cls), \
            f'Expect {cls.__name__}, but found {type(context.data).__name__} in context.data'
        return context.data

# endregion
