from typing import overload, Callable, Any, TypeVar

from ..framework import RecvContext, ExceptionContext, MessageHandler, EventHandler, ExceptionHandler
from .._commons import as_async

MessageEventHandler = TypeVar('MessageEventHandler', MessageHandler, EventHandler)


@overload
def resolve(
    *resolvers: Callable[[RecvContext], Any],
    **named_resolvers: Callable[[RecvContext], Any]
) -> Callable[[MessageEventHandler], MessageEventHandler]: pass


@overload
def resolve(
    *resolvers: Callable[[ExceptionContext], Any],
    **named_resolvers: Callable[[ExceptionContext], Any]
) -> Callable[[ExceptionHandler], ExceptionHandler]: pass


def resolve(*resolvers, **named_resolvers):
    def actual_decorator(handler):
        for resolver in resolvers:
            handler.resolvers[resolver.__name__] = as_async(resolver)
        for name, resolver in named_resolvers.items():
            handler.resolvers[name] = as_async(resolver)
        return handler

    return actual_decorator
