import copy
import types
from typing import Iterable, Callable, Awaitable, cast, Generic, TypeVar, Any

from ._context import RecvContext, ExceptionContext
from ..entities import Message, Event, MessageChain, Plain
from .._commons import get_class_attributes, invoke

__all__ = [
    'MessageHandler',
    'EventHandler',
    'ExceptionHandler'
]

Handler = TypeVar('Handler', bound='MessageHandler | EventHandler | ExceptionHandler')
Context = TypeVar('Context', RecvContext, ExceptionContext)
Data = TypeVar('Data', Message, Event, Exception)


class HandlerMixin(Generic[Handler, Context, Data]):
    def __init__(
        self,
        handler: Callable[..., str | MessageChain | None] | Callable[..., Awaitable[str | MessageChain | None]],
        types: Iterable[type[Data]],
        resolvers: dict[str, Callable[[Context], Any] | Callable[[Context], Awaitable]],
        filters: Iterable[Callable[[Context], bool] | Callable[[Context], Awaitable[bool]]] = (),
        before: Iterable[Handler] = (),
        after: Iterable[Handler] = ()
    ):
        self.handler = handler
        self.types = list(types)
        self.resolvers = resolvers
        self.filters = list(filters)
        self.before = list(before)
        self.after = list(after)
        self.attrname: str | None = None

    async def can_handle(self, context: Context) -> bool:
        for predicate in self.filters:
            if not await invoke(predicate, context):
                return False
        return True

    async def handle(self, context: Context) -> MessageChain | None:
        kwargs = {}
        for name, resolver in self.resolvers.items():
            kwargs[name] = await invoke(resolver, context)
        response = cast(str | MessageChain | None, await invoke(self.handler, **kwargs))
        return MessageChain([Plain(response)]) if isinstance(response, str) else response

    def __set_name__(self, owner: type, name: str):
        self.attrname = name

    def __get__(self, instance, owner: type | None = None) -> Handler:
        if instance is None:
            return cast(Handler, self)
        if self.attrname is None:
            raise TypeError
        if not hasattr(instance, '__dict__'):
            # not all objects have __dict__ (e.g. class defines slots)
            raise TypeError(f"No '__dict__' attribute on {type(instance).__name__!r} "
                            f'instance to cache {self.attrname!r} property.')
        handler = instance.__dict__.get(self.attrname)
        if handler is None:
            # id to attribute name
            class_attributes = {id(x): name for name, x in get_class_attributes(type(instance)).items()}

            def convert_before_after(lst: list[Handler]) -> list[Handler]:
                """Convert method handlers in 'before' and 'after' to bounded methods."""
                result = []
                for x in lst:
                    if id(x) in class_attributes:  # x is a handler method defined in current class
                        assert x.attrname is not None
                        result.append(getattr(instance, x.attrname))  # trigger __get__ of x
                    else:  # x is a handler function
                        if x.attrname is not None:
                            raise TypeError(f'{x.attrname!r} is a handler method '
                                            "but it isn't defined in current class.")
                        result.append(x)
                return result

            def convert_filters(filters: list[Callable]) -> list[Callable[[Context], Awaitable[bool]]]:
                result = []
                for x in filters:
                    if id(x) in class_attributes:
                        result.append(getattr(instance, class_attributes[id(x)]))
                    else:
                        result.append(x)
                return result

            def convert_resolvers(resolvers: dict[str, Callable]) -> dict[str, Callable[[Context], Awaitable]]:
                result = {}
                for name, x in resolvers.items():
                    if id(x) in class_attributes:
                        result[name] = getattr(instance, class_attributes[id(x)])
                    else:
                        result[name] = x
                return result

            handler = copy.copy(self)
            instance.__dict__[self.attrname] = handler
            # convert functions to bound methods
            handler.handler = handler.handler.__get__(instance, owner)
            handler.before = convert_before_after(handler.before)
            handler.after = convert_before_after(handler.after)
            handler.filters = convert_filters(handler.filters)
            handler.resolvers = convert_resolvers(handler.resolvers)
        return cast(Handler, handler)

    def __repr__(self) -> str:
        sb = [f'<{type(self).__name__}']
        if isinstance(self.handler, types.MethodType):
            sb.append(f'{self.handler.__qualname__} (bound method)')
        elif hasattr(self.handler, '__qualname__'):
            sb.append(self.handler.__qualname__)
        sb.append(f'at {hex(id(self))}>')
        return ' '.join(sb)


class MessageHandler(HandlerMixin['MessageHandler', RecvContext, Message]):
    pass


class EventHandler(HandlerMixin['EventHandler', RecvContext, Event]):
    pass


class ExceptionHandler(HandlerMixin['ExceptionHandler', ExceptionContext, Exception]):
    pass
