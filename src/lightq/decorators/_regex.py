import inspect
import re
import typing
from typing import Callable, TypeVar, cast

from ..framework import MessageHandler, ExceptionHandler, RecvContext, ExceptionContext
from ..entities import MessageChain
from .._commons import as_async

Handler = TypeVar('Handler', MessageHandler, ExceptionHandler)


def regex_match(
    pattern: str | re.Pattern[str],
    flags: int | re.RegexFlag = 0,
    extractor: Callable[[MessageChain], str] = MessageChain.__str__,
    matcher: Callable[[re.Pattern[str], str], re.Match[str] | None] = re.match
) -> Callable[[Handler], Handler]:
    pattern = re.compile(pattern, flags)

    def actual_decorator(handler: Handler) -> Handler:
        match: re.Match[str] | None = None

        async def is_match(context: RecvContext | ExceptionContext) -> bool:
            nonlocal match
            text = extractor(MessageChain.from_context(context))
            match = matcher(pattern, text)  # modify outer `match` variable
            return match is not None

        handler.filters.append(is_match)
        for name, param in inspect.signature(handler.handler).parameters.items():
            annotation = param.annotation
            if annotation == re.Match or typing.get_origin(annotation) == re.Match:
                handler.resolvers[name] = as_async(lambda ctx: match)
            elif name in pattern.groupindex:
                # if you use `lambda ctx: match[name]` here, then the captured
                # `name` of every lambda will be the same object (the last `name` in for loop).
                handler.resolvers[name] = as_async(
                    lambda ctx, name=name: cast(re.Match[str], match)[name]
                )
        return handler

    return actual_decorator


def regex_search(
    pattern: str | re.Pattern[str],
    flags: int | re.RegexFlag = 0,
    extractor: Callable[[MessageChain], str] = MessageChain.__str__
) -> Callable[[Handler], Handler]:
    return regex_match(pattern, flags, extractor, re.search)


def regex_fullmatch(
    pattern: str | re.Pattern[str],
    flags: int | re.RegexFlag = 0,
    extractor: Callable[[MessageChain], str] = MessageChain.__str__
) -> Callable[[Handler], Handler]:
    return regex_match(pattern, flags, extractor, re.fullmatch)
