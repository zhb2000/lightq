import inspect
import functools
from typing import Sequence, Callable, Awaitable, TypeVar, ParamSpec, cast

from ..entities import Message, Event, MessageChain, Plain
from ..framework import (
    MessageHandler,
    EventHandler,
    ExceptionHandler,
    RecvContext,
    ExceptionContext
)
from .._commons import as_async, invoke, is_class_annotation
from .._from_context import FromRecvContext, FromExceptionContext

T = TypeVar('T')
P = ParamSpec('P')


def to_sequence(obj: Sequence[T] | T) -> Sequence[T]:
    return obj if isinstance(obj, Sequence) else (obj,)


def message_handler(
    message_type: type[Message],
    *message_types: type[Message],
    filters: (Sequence[Callable[[RecvContext], bool] | Callable[[RecvContext], Awaitable[bool]]]
              | Callable[[RecvContext], bool]
              | Callable[[RecvContext], Awaitable[bool]]) = (),
    before: Sequence[MessageHandler] | MessageHandler = (),
    after: Sequence[MessageHandler] | MessageHandler = ()
) -> Callable[[Callable[..., str | MessageChain | None]
               | Callable[..., Awaitable[str | MessageChain | None]]],
              MessageHandler]:
    def actual_decorator(func: (Callable[P, str | MessageChain | None]
                                | Callable[P, Awaitable[str | MessageChain | None]])) -> MessageHandler:
        @functools.wraps(func)
        async def func_wrapper(*args: P.args, **kwargs: P.kwargs) -> MessageChain | None:
            result = cast(str | MessageChain | None, await invoke(func, *args, **kwargs))
            return MessageChain([Plain(result)]) if isinstance(result, str) else result

        handler = MessageHandler(
            handler=func_wrapper,
            message_types=[message_type, *message_types],
            resolvers=make_resolvers(func),
            filters=(
                cast(Callable[[RecvContext], Awaitable[bool]], as_async(f))
                for f in to_sequence(filters)
            ),
            before=to_sequence(before),
            after=to_sequence(after)
        )
        functools.update_wrapper(
            handler,
            func_wrapper,
            assigned=('__module__', '__name__', '__qualname__', '__doc__')
        )
        return handler

    return actual_decorator


def event_handler(
    event_type: type[Event],
    *event_types: type[Event],
    filters: (Sequence[Callable[[RecvContext], bool] | Callable[[RecvContext], Awaitable[bool]]]
              | Callable[[RecvContext], bool]
              | Callable[[RecvContext], Awaitable[bool]]) = (),
    before: Sequence[EventHandler] | EventHandler = (),
    after: Sequence[EventHandler] | EventHandler = ()
) -> Callable[[Callable[..., str | MessageChain | None]
               | Callable[..., Awaitable[str | MessageChain | None]]],
              EventHandler]:
    def actual_decorator(func: (Callable[P, str | MessageChain | None]
                                | Callable[P, Awaitable[str | MessageChain | None]])) -> EventHandler:
        @functools.wraps(func)
        async def func_wrapper(*args: P.args, **kwargs: P.kwargs) -> MessageChain | None:
            result = cast(str | MessageChain | None, await invoke(func, *args, **kwargs))
            return MessageChain([Plain(result)]) if isinstance(result, str) else result

        handler = EventHandler(
            handler=func_wrapper,
            event_types=[event_type, *event_types],
            resolvers=make_resolvers(func),
            filters=(
                cast(Callable[[RecvContext], Awaitable[bool]],as_async(f))
                for f in to_sequence(filters)
            ),
            before=to_sequence(before),
            after=to_sequence(after)
        )
        functools.update_wrapper(
            handler,
            func_wrapper,
            assigned=('__module__', '__name__', '__qualname__', '__doc__')
        )
        return handler

    return actual_decorator


def exception_handler(
    exception_type: type[Exception],
    *exception_types: type[Exception],
    filters: (Sequence[Callable[[ExceptionContext], bool] | Callable[[ExceptionContext], Awaitable[bool]]]
              | Callable[[ExceptionContext], bool]
              | Callable[[ExceptionContext], Awaitable[bool]]) = (),
    before: Sequence[ExceptionHandler] | ExceptionHandler = (),
    after: Sequence[ExceptionHandler] | ExceptionHandler = ()
) -> Callable[[Callable[..., str | MessageChain | None]
               | Callable[..., Awaitable[str | MessageChain | None]]],
              ExceptionHandler]:
    def actual_decorator(func: (Callable[P, str | MessageChain | None]
                                | Callable[P, Awaitable[str | MessageChain | None]])) -> ExceptionHandler:
        @functools.wraps(func)
        async def func_wrapper(*args: P.args, **kwargs: P.kwargs) -> MessageChain | None:
            result = cast(str | MessageChain | None, await invoke(func, *args, **kwargs))
            return MessageChain([Plain(result)]) if isinstance(result, str) else result

        handler = ExceptionHandler(
            handler=func_wrapper,
            exception_types=[exception_type, *exception_types],
            resolvers=make_resolvers_ex(func),
            filters=(
                cast(Callable[[ExceptionContext], Awaitable[bool]], as_async(f))
                for f in to_sequence(filters)
            ),
            before=to_sequence(before),
            after=to_sequence(after)
        )
        functools.update_wrapper(
            handler,
            func_wrapper,
            assigned=('__module__', '__name__', '__qualname__', '__doc__')
        )
        return handler

    return actual_decorator


def make_resolvers(func: Callable) -> dict[str, Callable[[RecvContext], Awaitable]]:
    resolvers = {}
    for name, param in inspect.signature(func).parameters.items():
        annotation = param.annotation
        if is_class_annotation(annotation) and issubclass(annotation, FromRecvContext):
            resolvers[name] = as_async(annotation.from_recv_context)
    return resolvers


def make_resolvers_ex(func: Callable) -> dict[str, Callable[[ExceptionContext], Awaitable]]:
    resolvers = {}
    for name, param in inspect.signature(func).parameters.items():
        annotation = param.annotation
        if is_class_annotation(annotation):
            if issubclass(annotation, FromExceptionContext):
                resolvers[name] = as_async(annotation.from_exception_context)
            elif issubclass(annotation, Exception):
                resolvers[name] = make_exception_resolver(annotation)
    return resolvers


def make_exception_resolver(cls: type[Exception]):
    async def exception_resolver(context: ExceptionContext):
        assert isinstance(context.exception, cls), \
            f'Expect {cls.__name__}, but get {type(context.exception).__name__} in context.exception'
        return context.exception

    return exception_resolver
