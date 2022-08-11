from typing import Callable, Type

from . import resolvers
from .framework import RecvContext, ExceptionContext, Bot
from .entities import MessageElement, MessageChain


def from_group(*group_id: int, all: bool = False) -> Callable[[RecvContext | ExceptionContext], bool]:
    group_set = set(group_id)

    def actual_filter(context: RecvContext | ExceptionContext) -> bool:
        gid = resolvers.get_group_id(context)
        if gid is None:
            return False
        return all or gid in group_set

    return actual_filter


def from_user(*user_id: int, all: bool = False) -> Callable[[RecvContext | ExceptionContext], bool]:
    user_set = set(user_id)

    def actual_filter(context: RecvContext | ExceptionContext) -> bool:
        uid = resolvers.get_sender_id(context)
        if uid is None:
            return False
        return all or uid in user_set

    return actual_filter


def chain_contains(item: MessageElement | Type[MessageElement]) -> Callable[[RecvContext | ExceptionContext], bool]:
    def actual_filter(context: RecvContext | ExceptionContext) -> bool:
        return item in MessageChain.from_context(context)

    return actual_filter


def is_at_user(user_id: int) -> Callable[[RecvContext | ExceptionContext], bool]:
    def actual_filter(context: RecvContext | ExceptionContext) -> bool:
        return user_id in resolvers.at_targets(context)

    return actual_filter


def is_at_bot(context: RecvContext | ExceptionContext) -> bool:
    bot_id = Bot.from_context(context).bot_id
    return bot_id in resolvers.at_targets(context)
