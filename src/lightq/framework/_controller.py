import abc
from typing import Callable, Iterable, Any, TypeVar

from ._handler import MessageHandler, EventHandler, ExceptionHandler

Handler = TypeVar('Handler', MessageHandler, EventHandler, ExceptionHandler)


class handler_property:
    def __init__(self, func: Callable[[Any], Handler]):
        self.func = func
        self.attrname: str | None = None
        self.__doc__ = func.__doc__
        self.cache: Handler | None = None

    def __set_name__(self, owner, name: str):
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                "Cannot assign the same handler_property to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "Cannot use handler_property instance without calling __set_name__ on it.")
        if self.cache is None:
            handler = self.func(instance)
            assert isinstance(handler, MessageHandler | EventHandler | ExceptionHandler), \
                'Expect a method which returns MessageHandler, EventHandler or ExceptionHandler ' \
                f'for handler_property, but the method returns {type(handler).__name__}.'
            self.cache = handler
        return self.cache


class Controller(abc.ABC):
    def __public_handler_property_names(self) -> Iterable[str]:
        cls = type(self)
        for attrname in dir(self):
            if attrname.startswith('_'):
                continue
            if isinstance(getattr(cls, attrname, None), handler_property):
                yield attrname

    @property
    def handlers(self) -> Iterable[MessageHandler | EventHandler | ExceptionHandler]:
        for attrname in self.__public_handler_property_names():
            if isinstance(getattr(self, attrname), MessageHandler | EventHandler | ExceptionHandler):
                yield getattr(self, attrname)

    @property
    def message_handlers(self) -> Iterable[MessageHandler]:
        for attrname in self.__public_handler_property_names():
            if isinstance(getattr(self, attrname), MessageHandler):
                yield getattr(self, attrname)

    @property
    def event_handlers(self) -> Iterable[EventHandler]:
        for attrname in self.__public_handler_property_names():
            if isinstance(getattr(self, attrname), EventHandler):
                yield getattr(self, attrname)

    @property
    def exception_handlers(self) -> Iterable[ExceptionHandler]:
        for attrname in self.__public_handler_property_names():
            if isinstance(getattr(self, attrname), ExceptionHandler):
                yield getattr(self, attrname)
