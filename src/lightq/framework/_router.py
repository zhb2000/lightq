import inspect
import abc
from typing import Iterable, TypeVar, Generic, cast

from ..entities import Message, Event
from ._context import RecvContext, ExceptionContext
from ._handler import MessageHandler, EventHandler, ExceptionHandler

__all__ = [
    'MessageRouter',
    'EventRouter',
    'ExceptionRouter',
    'MessageTypeRouter',
    'EventTypeRouter',
    'ExceptionTypeRouter'
]


class MessageRouter(abc.ABC):
    before: list['MessageRouter']
    after: list['MessageRouter']

    @abc.abstractmethod
    def build(self, handlers: Iterable[MessageHandler]): pass

    @abc.abstractmethod
    def clear(self): pass

    @abc.abstractmethod
    async def route(self, context: RecvContext) -> MessageHandler | None: pass


class EventRouter(abc.ABC):
    before: list['EventRouter']
    after: list['EventRouter']

    @abc.abstractmethod
    def build(self, handlers: Iterable[EventHandler]): pass

    @abc.abstractmethod
    def clear(self): pass

    @abc.abstractmethod
    async def route(self, context: RecvContext) -> EventHandler | None: pass


class ExceptionRouter(abc.ABC):
    before: list['ExceptionRouter']
    after: list['ExceptionRouter']

    @abc.abstractmethod
    def build(self, handlers: Iterable[ExceptionHandler]): pass

    @abc.abstractmethod
    def clear(self): pass

    @abc.abstractmethod
    async def route(self, context: ExceptionContext) -> ExceptionHandler | None: pass


Handler = TypeVar('Handler', MessageHandler, EventHandler, ExceptionHandler)
Data = TypeVar('Data', Message, Event, Exception)


class TypeRouterMixin(Generic[Handler, Data]):
    def __init__(self):
        self.type_to_handlers: dict[type[Data], list[Handler]] = {}

    def build(self, handlers: Iterable[Handler]):
        self.clear()
        for handler in handlers:
            for cls in cast(list[type[Data]], handler.types):
                if cls not in self.type_to_handlers:
                    self.type_to_handlers[cls] = []
                self.type_to_handlers[cls].append(handler)

    def clear(self):
        self.type_to_handlers.clear()

    async def _route_by_exact_type(self, cls: type, context) -> Handler | None:
        if cls in self.type_to_handlers:
            for handler in self.type_to_handlers[cast(type[Data], cls)]:
                if await handler.can_handle(context):
                    return handler
        return None

    async def _route_by_mro(self, cls: type, context) -> Handler | None:
        for cls in inspect.getmro(cls):
            handler = await self._route_by_exact_type(cls, context)
            if handler is not None:
                return handler
        return None


class MessageTypeRouter(TypeRouterMixin[MessageHandler, Message], MessageRouter):
    def __init__(
        self,
        before: Iterable[MessageRouter] = (),
        after: Iterable[MessageRouter] = ()
    ):
        TypeRouterMixin.__init__(self)
        self.before = list(before)
        self.after = list(after)

    async def route(self, context: RecvContext) -> MessageHandler | None:
        return await super()._route_by_mro(type(context.data), context)


class EventTypeRouter(TypeRouterMixin[EventHandler, Event], EventRouter):
    def __init__(
        self,
        before: Iterable[EventRouter] = (),
        after: Iterable[EventRouter] = ()
    ):
        TypeRouterMixin.__init__(self)
        self.before = list(before)
        self.after = list(after)

    async def route(self, context: RecvContext) -> EventHandler | None:
        return await super()._route_by_mro(type(context.data), context)


class ExceptionTypeRouter(TypeRouterMixin[ExceptionHandler, Exception], ExceptionRouter):
    def __init__(
        self,
        before: Iterable[ExceptionRouter] = (),
        after: Iterable[ExceptionRouter] = ()
    ):
        TypeRouterMixin.__init__(self)
        self.before = list(before)
        self.after = list(after)

    async def route(self, context: ExceptionContext) -> ExceptionHandler | None:
        return await super()._route_by_mro(type(context.exception), context)
