import inspect
import datetime
import asyncio
import typing
import functools
from collections import deque
from typing import Callable, overload, Awaitable, TypeVar, ParamSpec, Any, Coroutine

T = TypeVar('T')
P = ParamSpec('P')


@overload
def remove_if(container: list[T], predicate: Callable[[T], bool]) -> T | None: pass


@overload
def remove_if(container: deque[T], predicate: Callable[[T], bool]) -> T | None: pass


@overload
def remove_if(container: set[T], predicate: Callable[[T], bool]) -> T | None: pass


def remove_if(container: list[T] | deque[T] | set[T], predicate: Callable[[T], bool]) -> T | None:
    if isinstance(container, set):
        for element in container:
            if predicate(element):
                container.remove(element)
                return element
        return None
    else:
        for i, element in enumerate(container):
            if predicate(element):
                del container[i]
                return element
        return None


class AutoIncrement:
    def __init__(self, start: int = 0, max_value: int | None = None):
        self.__current = start
        self.__max_value = max_value

    def get(self) -> int:
        ret = self.__current
        self.__current += 1
        if self.__max_value is not None and self.__current > self.__max_value:
            self.__current = 0
        return ret


def to_camel_case(snake_case: str) -> str:
    """
    snake_case to camelCase

    Examples:
    ::
        to_camel_case('my_name') == 'myName'
    """
    if snake_case == 'from_':
        return 'from'
    words = snake_case.split('_')
    words[1:] = [f'{w[0].upper()}{w[1:]}' for w in words[1:]]
    return ''.join(words)


def to_snake_case(camel_case: str) -> str:
    """
    camelCase to snake_case

    Examples:
    ::
        to_snake_case('myName') == 'my_name'
    """
    if camel_case == 'from':
        return 'from_'
    words = []
    temp_word = []
    for i, ch in enumerate(camel_case):
        if ch.isupper():
            is_word_begin = (i + 1 < len(camel_case) and camel_case[i + 1].islower()) \
                            or (i > 0 and camel_case[i - 1].islower())
            if is_word_begin and len(temp_word) > 0:
                words.append(''.join(temp_word))
                temp_word.clear()
        temp_word.append(ch)
    if len(temp_word) > 0:
        words.append(''.join(temp_word))
    return '_'.join(w.lower() for w in words)


@overload
async def invoke(func: Callable[P, Coroutine[Any, Any, T]], *args: P.args, **kwargs: P.kwargs) -> T: pass


@overload
async def invoke(func: Callable[P, Awaitable[T]], *args: P.args, **kwargs: P.kwargs) -> T: pass


@overload
async def invoke(func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T: pass


async def invoke(func: Callable, *args, **kwargs):
    result = func(*args, **kwargs)
    return (await result) if inspect.isawaitable(result) else result


@overload
def as_async(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Awaitable[T]]: pass


@overload
def as_async(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: pass


@overload
def as_async(func: Callable[P, T]) -> Callable[P, Awaitable[T]]: pass


def as_async(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await invoke(func, *args, **kwargs)

    return wrapper


def is_class_annotation(obj: Any) -> bool:
    # inspect.isclass(list[T]) == True, typing.get_origin(list[T]) == T
    # inspect.isclass(list) == True, typing.get_origin(list) is None
    return inspect.isclass(obj) and typing.get_origin(obj) is None


async def sleep_until(until: datetime.datetime):
    now = datetime.datetime.now(until.tzinfo)
    await asyncio.sleep((until - now).total_seconds())


async def do_everyday(time: datetime.time, action: Callable[[], Awaitable] | Callable[[], Any]):
    now = datetime.datetime.now(time.tzinfo)
    until = datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=time.hour,
        minute=time.minute,
        second=time.second,
        microsecond=time.microsecond,
        tzinfo=time.tzinfo
    )
    if until <= now:
        until = until + datetime.timedelta(days=1)
    while True:
        await sleep_until(until)
        await invoke(action)
        until = until + datetime.timedelta(days=1)
