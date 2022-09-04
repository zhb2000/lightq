import abc
import typing
from typing import TypeVar, Type

if typing.TYPE_CHECKING:
    from .framework import RecvContext, ExceptionContext

__all__ = ['FromRecvContext', 'FromExceptionContext', 'FromContext']

Self = TypeVar('Self')


class FromRecvContext(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_recv_context(cls: Type[Self], context: 'RecvContext') -> Self:
        raise NotImplementedError


class FromExceptionContext(abc.ABC):
    @classmethod
    def from_exception_context(cls: Type[Self], context: 'ExceptionContext') -> Self:
        if issubclass(cls, FromRecvContext):
            return cls.from_recv_context(context.context)
        raise NotImplementedError


FromContextSelf = TypeVar('FromContextSelf', bound='FromContext')


class FromContext(FromRecvContext, FromExceptionContext, abc.ABC):
    @classmethod
    def from_context(cls: Type[FromContextSelf], context: 'RecvContext | ExceptionContext') -> FromContextSelf:
        from .framework import RecvContext
        if isinstance(context, RecvContext):
            return cls.from_recv_context(context)
        else:
            return cls.from_exception_context(context)
