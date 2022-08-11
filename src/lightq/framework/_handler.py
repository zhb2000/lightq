from typing import Iterable, Callable, Awaitable

from ._context import RecvContext, ExceptionContext
from ..entities import Message, Event, MessageChain

__all__ = [
    'MessageHandler',
    'EventHandler',
    'ExceptionHandler'
]


async def can_handle(self, context) -> bool:
    for predicate in self.filters:
        if not await predicate(context):
            return False
    return True


async def handle(self, context) -> MessageChain | None:
    kwargs = {}
    for name, resolver in self.resolvers.items():
        kwargs[name] = await resolver(context)
    return await self.handler(**kwargs)


class MessageHandler:
    def __init__(
        self,
        handler: Callable[..., Awaitable[MessageChain | None]],
        message_types: Iterable[type[Message]],
        resolvers: dict[str, Callable[[RecvContext], Awaitable]],
        filters: Iterable[Callable[[RecvContext], Awaitable[bool]]] = (),
        before: Iterable['MessageHandler'] = (),
        after: Iterable['MessageHandler'] = ()
    ):
        self.handler = handler
        self.types = list(message_types)
        self.resolvers = resolvers
        self.filters = list(filters)
        self.before = list(before)
        self.after = list(after)

    async def can_handle(self, context: RecvContext) -> bool:
        return await can_handle(self, context)

    async def handle(self, context: RecvContext) -> MessageChain | None:
        return await handle(self, context)


class EventHandler:
    def __init__(
        self,
        handler: Callable[..., Awaitable[MessageChain | None]],
        event_types: Iterable[type[Event]],
        resolvers: dict[str, Callable[[RecvContext], Awaitable]],
        filters: Iterable[Callable[[RecvContext], Awaitable[bool]]] = (),
        before: Iterable['EventHandler'] = (),
        after: Iterable['EventHandler'] = ()
    ):
        self.handler = handler
        self.types = list(event_types)
        self.resolvers = resolvers
        self.filters = list(filters)
        self.before = list(before)
        self.after = list(after)

    async def can_handle(self, context: RecvContext) -> bool:
        return await can_handle(self, context)

    async def handle(self, context: RecvContext) -> MessageChain | None:
        return await handle(self, context)


class ExceptionHandler:
    def __init__(
        self,
        handler: Callable[..., Awaitable[MessageChain | None]],
        exception_types: Iterable[type[Exception]],
        resolvers: dict[str, Callable[[ExceptionContext], Awaitable]],
        filters: Iterable[Callable[[ExceptionContext], Awaitable[bool]]] = (),
        before: Iterable['ExceptionHandler'] = (),
        after: Iterable['ExceptionHandler'] = ()
    ):
        self.handler = handler
        self.types = list(exception_types)
        self.resolvers = resolvers
        self.filters = list(filters)
        self.before = list(before)
        self.after = list(after)

    async def can_handle(self, context: ExceptionContext) -> bool:
        return await can_handle(self, context)

    async def handle(self, context: ExceptionContext) -> MessageChain | None:
        return await handle(self, context)
