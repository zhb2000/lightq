import typing
import abc
from typing import Union

from ..entities import Message, Event, SyncMessage, UnsupportedEntity
from .._from_context import FromExceptionContext, FromContext

if typing.TYPE_CHECKING:
    from ._bot import Bot
    from ._handler import MessageHandler, EventHandler


class Context(abc.ABC):
    def __init__(self, bot: 'Bot'):
        self.bot = bot


class RecvContext(Context, FromContext):
    def __init__(
        self,
        bot: 'Bot',
        data: Message | Event | SyncMessage | UnsupportedEntity
    ):
        super().__init__(bot)
        self.data = data

    @classmethod
    def from_recv_context(cls, context: 'RecvContext') -> 'RecvContext':
        return context


class ExceptionContext(Context, FromExceptionContext):
    def __init__(
        self,
        exception: Exception,
        context: RecvContext,
        handler: Union['MessageHandler', 'EventHandler', None],
    ):
        super().__init__(context.bot)
        self.exception = exception
        self.context = context
        self.handler = handler

    @classmethod
    def from_exception_context(cls, context: 'ExceptionContext') -> 'ExceptionContext':
        return context
