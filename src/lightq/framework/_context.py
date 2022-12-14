import typing

from ..entities import Message, Event, SyncMessage, UnsupportedEntity
from .._from_context import FromExceptionContext, FromContext

if typing.TYPE_CHECKING:
    from ._bot import Bot
    from ._handler import MessageHandler, EventHandler


class RecvContext(FromContext):
    def __init__(
        self,
        bot: 'Bot',
        data: Message | Event | SyncMessage | UnsupportedEntity
    ):
        self.bot = bot
        self.data = data

    @classmethod
    def from_recv_context(cls, context: 'RecvContext') -> 'RecvContext':
        return context


class ExceptionContext(FromExceptionContext):
    def __init__(
        self,
        exception: Exception,
        context: RecvContext,
        handler: 'MessageHandler | EventHandler | None',
    ):
        self.bot = context.bot
        self.exception = exception
        self.context = context
        self.handler = handler

    @classmethod
    def from_exception_context(cls, context: 'ExceptionContext') -> 'ExceptionContext':
        return context
