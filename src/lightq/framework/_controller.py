import abc
from typing import Callable, Iterable, Any, TypeVar

from ._handler import MessageHandler, EventHandler, ExceptionHandler
from .._commons import get_class_attributes

Handler = TypeVar('Handler', MessageHandler, EventHandler, ExceptionHandler)


class handler_property:
    def __init__(self, func: Callable[[Any], Handler]):
        self.func = func
        self.attrname: str | None = None
        self.__doc__ = func.__doc__

    def __set_name__(self, owner: type, name: str):
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                'Cannot assign the same handler_property to two different names '
                f'({self.attrname!r} and {name!r}).'
            )

    def __get__(self, instance, owner: type | None = None):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError('Cannot use handler_property instance without '
                            'calling __set_name__ on it.')
        if not hasattr(instance, '__dict__'):
            # not all objects have __dict__ (e.g. class defines slots)
            raise TypeError(f"No '__dict__' attribute on {type(instance).__name__!r} "
                            f'instance to cache {self.attrname!r} property.')
        handler = instance.__dict__.get(self.attrname)
        if handler is None:
            handler = self.func(instance)
            instance.__dict__[self.attrname] = handler
        return handler


class Controller(abc.ABC):
    @property
    def handlers(self) -> Iterable[MessageHandler | EventHandler | ExceptionHandler]:
        for name, value in get_class_attributes(type(self)).items():
            if not name.startswith('_') and isinstance(
                value,
                MessageHandler | EventHandler | ExceptionHandler | handler_property
            ):
                yield getattr(self, name)

    @property
    def message_handlers(self) -> Iterable[MessageHandler]:
        for handler in self.handlers:
            if isinstance(handler, MessageHandler):
                yield handler

    @property
    def event_handlers(self) -> Iterable[EventHandler]:
        for handler in self.handlers:
            if isinstance(handler, EventHandler):
                yield handler

    @property
    def exception_handlers(self) -> Iterable[ExceptionHandler]:
        for handler in self.handlers:
            if isinstance(handler, ExceptionHandler):
                yield handler
