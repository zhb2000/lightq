from typing import overload, Callable, Any, TypeVar

from ..framework import RecvContext, ExceptionContext, MessageHandler, EventHandler, ExceptionHandler

MessageEventHandler = TypeVar('MessageEventHandler', MessageHandler, EventHandler)


@overload
def resolve(
    *resolvers: Callable[[RecvContext], Any] | Callable[[Any, RecvContext], Any],
    **named_resolvers: Callable[[RecvContext], Any] | Callable[[Any, RecvContext], Any]
) -> Callable[[MessageEventHandler], MessageEventHandler]: pass


@overload
def resolve(
    *resolvers: Callable[[ExceptionContext], Any] | Callable[[Any, ExceptionContext], Any],
    **named_resolvers: Callable[[ExceptionContext], Any] | Callable[[Any, ExceptionContext], Any]
) -> Callable[[ExceptionHandler], ExceptionHandler]: pass


def resolve(*resolvers, **named_resolvers) -> Callable:
    def actual_decorator(handler):
        for resolver in resolvers:
            handler.resolvers[resolver.__name__] = resolver
        for name, resolver in named_resolvers.items():
            handler.resolvers[name] = resolver
        return handler

    return actual_decorator
