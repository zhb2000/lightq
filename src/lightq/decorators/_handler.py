import inspect
import functools
from typing import Sequence, Callable, Awaitable, TypeVar, Any, cast

from ..entities import Message, Event, MessageChain
from ..framework import (
    MessageHandler,
    EventHandler,
    ExceptionHandler,
    RecvContext,
    ExceptionContext
)
from .._commons import is_class_annotation
from .._from_context import FromRecvContext, FromExceptionContext

T = TypeVar('T')
# Don't update handler's __annotations__
WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__', '__doc__')


def to_sequence(obj: Sequence[T] | T) -> Sequence[T]:
    return obj if isinstance(obj, Sequence) else (obj,)


def message_handler(
    message_type: type[Message],
    *message_types: type[Message],
    filters: (Sequence[Callable[[RecvContext], bool]
                       | Callable[[RecvContext], Awaitable[bool]]
                       | Callable[[Any, RecvContext], bool]
                       | Callable[[Any, RecvContext], Awaitable[bool]]]
              | Callable[[RecvContext], bool]
              | Callable[[RecvContext], Awaitable[bool]]
              | Callable[[Any, RecvContext], bool]
              | Callable[[Any, RecvContext], Awaitable[bool]]) = (),
    before: Sequence[MessageHandler] | MessageHandler = (),
    after: Sequence[MessageHandler] | MessageHandler = ()
) -> Callable[[Callable[..., str | MessageChain | None]
               | Callable[..., Awaitable[str | MessageChain | None]]],
              MessageHandler]:
    def actual_decorator(func: (Callable[..., str | MessageChain | None]
                                | Callable[..., Awaitable[str | MessageChain | None]])) -> MessageHandler:
        handler = MessageHandler(
            handler=func,
            types=[message_type, *message_types],
            resolvers=make_resolvers(func),
            filters=cast(Sequence[Callable], to_sequence(filters)),
            before=to_sequence(before),
            after=to_sequence(after)
        )
        functools.update_wrapper(handler, func, assigned=WRAPPER_ASSIGNMENTS)
        return handler

    return actual_decorator


def event_handler(
    event_type: type[Event],
    *event_types: type[Event],
    filters: (Sequence[Callable[[RecvContext], bool]
                       | Callable[[RecvContext], Awaitable[bool]]
                       | Callable[[Any, RecvContext], bool]
                       | Callable[[Any, RecvContext], Awaitable[bool]]]
              | Callable[[RecvContext], bool]
              | Callable[[RecvContext], Awaitable[bool]]
              | Callable[[Any, RecvContext], bool]
              | Callable[[Any, RecvContext], Awaitable[bool]]) = (),
    before: Sequence[EventHandler] | EventHandler = (),
    after: Sequence[EventHandler] | EventHandler = ()
) -> Callable[[Callable[..., str | MessageChain | None]
               | Callable[..., Awaitable[str | MessageChain | None]]],
              EventHandler]:
    def actual_decorator(func: (Callable[..., str | MessageChain | None]
                                | Callable[..., Awaitable[str | MessageChain | None]])) -> EventHandler:
        handler = EventHandler(
            handler=func,
            types=[event_type, *event_types],
            resolvers=make_resolvers(func),
            filters=cast(Sequence[Callable], to_sequence(filters)),
            before=to_sequence(before),
            after=to_sequence(after)
        )
        functools.update_wrapper(handler, func, assigned=WRAPPER_ASSIGNMENTS)
        return handler

    return actual_decorator


def exception_handler(
    exception_type: type[Exception],
    *exception_types: type[Exception],
    filters: (Sequence[Callable[[ExceptionContext], bool]
                       | Callable[[ExceptionContext], Awaitable[bool]]
                       | Callable[[Any, ExceptionContext], bool]
                       | Callable[[Any, ExceptionHandler], Awaitable[bool]]]
              | Callable[[ExceptionContext], bool]
              | Callable[[ExceptionContext], Awaitable[bool]]
              | Callable[[Any, ExceptionContext], bool]
              | Callable[[Any, ExceptionHandler], Awaitable[bool]]) = (),
    before: Sequence[ExceptionHandler] | ExceptionHandler = (),
    after: Sequence[ExceptionHandler] | ExceptionHandler = ()
) -> Callable[[Callable[..., str | MessageChain | None]
               | Callable[..., Awaitable[str | MessageChain | None]]],
              ExceptionHandler]:
    def actual_decorator(func: (Callable[..., str | MessageChain | None]
                                | Callable[..., Awaitable[str | MessageChain | None]])) -> ExceptionHandler:
        handler = ExceptionHandler(
            handler=func,
            types=[exception_type, *exception_types],
            resolvers=make_resolvers_ex(func),
            filters=cast(Sequence[Callable], to_sequence(filters)),
            before=to_sequence(before),
            after=to_sequence(after)
        )
        functools.update_wrapper(handler, func, assigned=WRAPPER_ASSIGNMENTS)
        return handler

    return actual_decorator


def make_resolvers(func: Callable) -> dict[str, Callable[[RecvContext], Any]]:
    """Make type-based resolvers."""
    resolvers = {}
    for name, param in inspect.signature(func).parameters.items():
        annotation = param.annotation
        if is_class_annotation(annotation) and issubclass(annotation, FromRecvContext):
            resolvers[name] = annotation.from_recv_context
    return resolvers


def make_resolvers_ex(func: Callable) -> dict[str, Callable[[ExceptionContext], Any]]:
    resolvers = {}
    for name, param in inspect.signature(func).parameters.items():
        annotation = param.annotation
        if is_class_annotation(annotation):
            if issubclass(annotation, FromExceptionContext):
                resolvers[name] = annotation.from_exception_context
            elif issubclass(annotation, Exception):
                resolvers[name] = make_exception_resolver(annotation)
    return resolvers


def make_exception_resolver(cls: type[Exception]) -> Callable[[ExceptionContext], Exception]:
    def exception_resolver(context: ExceptionContext) -> Exception:
        assert isinstance(context.exception, cls), \
            f'Expect {cls.__name__}, but get {type(context.exception).__name__} in context.exception'
        return context.exception

    return exception_resolver
