import asyncio
import datetime
import itertools
import functools
from typing import Iterable, overload, Callable, Awaitable, Any, TypeVar, Coroutine, cast

from .. import _commons, entities
from ._router import (
    MessageRouter,
    EventRouter,
    ExceptionRouter,
    MessageTypeRouter,
    EventTypeRouter,
    ExceptionTypeRouter
)
from ._context import RecvContext, ExceptionContext
from ._handler import MessageHandler, EventHandler, ExceptionHandler
from ..api import MiraiApi
from ..entities import Message, Event, MessageChain
from ..exceptions import MiraiApiException
from .._from_context import FromContext
from ..logging import logger

T = TypeVar('T')


class Bot(FromContext):
    def __init__(
        self,
        bot_id: int,
        verify_key: str,
        base_url: str = 'ws://localhost:8080',
        reserved_sync_id: str = '-1'
    ):
        self.__api = MiraiApi(bot_id, verify_key, base_url, reserved_sync_id)
        self.message_handlers: list[MessageHandler] = []
        self.event_handlers: list[EventHandler] = []
        self.default_exception_handler = make_default_exception_handler()
        self.exception_handlers: list[ExceptionHandler] = [self.default_exception_handler]
        self.default_message_router = MessageTypeRouter()
        self.message_routers: list[MessageRouter] = [self.default_message_router]
        self.default_event_router = EventTypeRouter()
        self.event_routers: list[EventRouter] = [self.default_event_router]
        self.default_exception_router = ExceptionTypeRouter()
        self.exception_routers: list[ExceptionRouter] = [self.default_exception_router]
        self.__message_handler_orders: list[tuple[MessageHandler, MessageHandler]] = []
        self.__event_handler_orders: list[tuple[EventHandler, EventHandler]] = []
        self.__exception_handler_orders: list[tuple[ExceptionHandler, ExceptionHandler]] = []
        self.__message_router_orders: list[tuple[MessageRouter, MessageRouter]] = []
        self.__event_router_orders: list[tuple[EventRouter, EventRouter]] = []
        self.__exception_router_orders: list[tuple[ExceptionRouter, ExceptionRouter]] = []
        self.__background_tasks: set[asyncio.Task] = set()

    @property
    def api(self) -> MiraiApi: return self.__api

    @property
    def bot_id(self) -> int: return self.__api.bot_id

    @property
    def verify_key(self) -> str: return self.__api.verify_key

    @property
    def base_url(self) -> str: return self.__api.base_url

    @property
    def reserved_sync_id(self) -> str: return self.__api.reserved_sync_id

    def add(self, item: MessageHandler | EventHandler | ExceptionHandler
                        | MessageRouter | EventRouter | ExceptionRouter):
        match item:
            case MessageHandler():
                self.message_handlers.append(item)
            case EventHandler():
                self.event_handlers.append(item)
            case ExceptionHandler():
                self.exception_handlers.append(item)
            case MessageRouter():
                self.message_routers.append(item)
            case EventRouter():
                self.event_routers.append(item)
            case ExceptionRouter():
                self.exception_routers.append(item)
            case _:
                raise TypeError(f'Unsupported type: {type(item)}')

    def add_all(self, items: Iterable[MessageHandler | EventHandler | ExceptionHandler
                                      | MessageRouter | EventRouter | ExceptionRouter]):
        for item in items:
            self.add(item)

    async def close(self):
        await self.__api.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def create_task(self, coro: Coroutine[Any, Any, T], *, name: str | None = None) -> asyncio.Task[T]:
        task = asyncio.create_task(coro, name=name)
        self.__background_tasks.add(task)
        task.add_done_callback(self.__background_tasks.discard)
        return task

    def create_everyday_task(
        self,
        time: datetime.time,
        action: Callable[[], Awaitable] | Callable[[], Any],
        *,
        name: str | None = None
    ) -> asyncio.Task:
        return self.create_task(_commons.do_everyday(time, action), name=name)

    async def run(self):
        self.build()
        try:
            async for data in self.__api:
                context = RecvContext(self, data)
                background_func = self.__make_background_func(context)
                self.create_task(background_func())
        finally:
            await self.close()

    def __make_background_func(self, context: RecvContext) -> Callable[[], Coroutine[Any, Any, None]]:
        async def handle_recv_data():
            try:
                handler = await self.__get_handler(context)
                if handler is None:
                    return
            except Exception as e:  # exception from router, without handler
                if await self.__handle_exception(ExceptionContext(e, context, handler=None)):
                    return
                raise
            try:
                response = await handler.handle(context)
                if response is None:
                    return
                await self.__send_to_sender(context.data, response)
            except Exception as e:  # exception from handler
                if await self.__handle_exception(ExceptionContext(e, context, handler)):
                    return
                raise

        return handle_recv_data

    async def __handle_exception(self, context: ExceptionContext) -> bool:
        handler = await self.__get_handler(context)
        if handler is None:
            return False
        try:
            response = await handler.handle(context)
        except MiraiApiException as e:  # swallow and log MiraiApiException
            logger.error('swallow an exception raised from an exception handler, '
                         f'exception: {repr(e)}, exception handler: {handler}')
            return True
        if response is not None:
            try:
                await self.__send_to_sender(context.context.data, response)
            except MiraiApiException as e:  # swallow and log MiraiApiException
                logger.error('swallow an exception while sending the response from an exception handler, '
                             f'exception: {repr(e)}, exception handler: {handler}')
        return True

    @overload
    async def __get_handler(self, context: RecvContext) -> MessageHandler | EventHandler | None: pass

    @overload
    async def __get_handler(self, context: ExceptionContext) -> ExceptionHandler | None: pass

    async def __get_handler(
        self,
        context: RecvContext | ExceptionContext
    ) -> MessageHandler | EventHandler | ExceptionHandler | None:
        match context:
            case RecvContext(data=Message()):
                routers = self.message_routers
            case RecvContext(data=Event()):
                routers = self.event_routers
            case ExceptionContext():
                routers = self.exception_routers
            case _:
                return None
        for router in routers:
            handler = await router.route(context)
            if handler is not None:
                return handler
        return None

    async def __send_to_sender(
        self,
        data: Message | Event | entities.SyncMessage | entities.UnsupportedEntity,
        message: MessageChain
    ):
        if isinstance(data, Event):
            if hasattr(data, 'group') and isinstance(data.group, entities.Group):
                await self.api.send_group_message(data.group.id, message)
            elif hasattr(data, 'operator') and isinstance(data.operator, entities.Member):
                await self.api.send_group_message(data.operator.group.id, message)
            elif hasattr(data, 'member') and isinstance(data.member, entities.Member):
                await self.api.send_group_message(data.member.group.id, message)
            elif hasattr(data, 'friend') and isinstance(data.friend, entities.Friend):
                await self.api.send_friend_message(data.friend.id, message)
            elif isinstance(data, entities.FriendRecallEvent):
                await self.api.send_friend_message(data.author_id, message)
            elif isinstance(data, entities.NudgeEvent):
                if data.subject.kind == 'Group':
                    await self.api.send_group_message(data.subject.id, message)
                elif data.subject.kind == 'Friend':
                    await self.api.send_friend_message(data.subject.id, message)
        elif isinstance(data, entities.GroupMessage):
            await self.api.send_group_message(data.sender.group.id, message)
        elif isinstance(data, entities.FriendMessage):
            await self.api.send_friend_message(data.sender.id, message)
        elif isinstance(data, entities.TempMessage):
            await self.api.send_temp_message(data.sender.id, data.sender.group.id, message)

    def build(self):
        self.clear()
        self.message_handlers = bot_topo_sort(self.message_handlers, self.__message_handler_orders)
        self.event_handlers = bot_topo_sort(self.event_handlers, self.__event_handler_orders)
        self.exception_handlers = bot_topo_sort(
            self.exception_handlers,
            self.__exception_handler_orders,
            self.default_exception_handler
        )
        self.message_routers = bot_topo_sort(
            self.message_routers,
            self.__message_router_orders,
            self.default_message_router)
        self.event_routers = bot_topo_sort(
            self.event_routers,
            self.__event_router_orders,
            self.default_event_router
        )
        self.exception_routers = bot_topo_sort(
            self.exception_routers,
            self.__exception_router_orders,
            self.default_exception_router
        )
        for router in self.message_routers:
            router.build(self.message_handlers)
        for router in self.event_routers:
            router.build(self.event_handlers)
        for router in self.exception_routers:
            router.build(self.exception_handlers)

    def clear(self):
        for router in itertools.chain(
            self.message_routers,
            self.event_routers,
            self.exception_routers
        ):
            router.clear()

    @overload
    def add_order(self, item1: MessageHandler, item2: MessageHandler, /, *rest: MessageHandler): pass

    @overload
    def add_order(self, item1: EventHandler, item2: EventHandler, /, *rest: EventHandler): pass

    @overload
    def add_order(self, item1: ExceptionHandler, item2: ExceptionHandler, /, *rest: ExceptionHandler): pass

    @overload
    def add_order(self, item1: MessageRouter, item2: MessageRouter, /, *rest: MessageRouter): pass

    @overload
    def add_order(self, item1: EventRouter, item2: EventRouter, /, *rest: EventRouter): pass

    @overload
    def add_order(self, item1: ExceptionRouter, item2: ExceptionRouter, /, *rest: ExceptionRouter): pass

    def add_order(self, item1, item2, /, *rest):
        items = [item1, item2, *rest]
        match item1:
            case MessageHandler(): orders = self.__message_handler_orders
            case EventHandler(): orders = self.__event_handler_orders
            case ExceptionHandler(): orders = self.__exception_handler_orders
            case MessageRouter(): orders = self.__message_router_orders
            case EventRouter(): orders = self.__event_router_orders
            case ExceptionRouter(): orders = self.__exception_router_orders
            case _: raise TypeError(f'Unsupported type: {type(item1)}')
        orders.extend(itertools.pairwise(items))

    @classmethod
    def from_recv_context(cls, context: RecvContext) -> 'Bot':
        return context.bot


def make_default_exception_handler() -> ExceptionHandler:
    async def handler(context: ExceptionContext):
        if context.handler is not None:
            logger.error('swallow an exception from an handler, '
                         f'exception: {repr(context.exception)}, handler: {repr(context.handler)}')
        else:
            logger.error('swallow an exception while routing received data, '
                         f'exception: {repr(context.exception)}')

    return ExceptionHandler(
        handler,
        exception_types=[MiraiApiException],
        resolvers={'context': _commons.as_async(ExceptionContext.from_exception_context)}
    )


def topological_sort(items: Iterable[T], orders: Iterable[tuple[T, T]]) -> list[T] | None:
    # out neighbors
    graph: dict[T, list[T]] = {u: [] for u in items}
    for u, v in orders:
        assert u in graph and v in graph
        graph[u].append(v)
    vis = {u: 0 for u in items}
    topo = []

    def dfs(u: T) -> bool:
        vis[u] = -1
        for v in graph[u]:
            if vis[v] == -1:
                return False
            elif vis[v] == 0:
                if not dfs(v):
                    return False
        vis[u] = 1
        topo.append(u)
        return True

    for u in graph:
        if vis[u] == 0:
            if not dfs(u):
                return None  # Cannot topological sort.
    topo.reverse()
    return topo


def bot_topo_sort(
    items: list[T],
    extra_orders: list[tuple[T, T]],
    default: T | None = None
) -> list[T]:
    orders: list[tuple[T, T]] = []
    for item in items:
        orders.extend((item, x) for x in item.before)
        orders.extend((x, item) for x in item.after)
    orders.extend(extra_orders)
    if default is not None:
        if topological_sort(items, orders) is None:  # check if there is a circle
            raise Exception('Cannot topological sort.')
        out_neighbors: dict[T, list[T]] = {item: [] for item in items}
        in_neighbors: dict[T, list[T]] = {item: [] for item in items}
        for u, v in orders:  # u -> v, v must be placed after u
            out_neighbors[u].append(v)
            in_neighbors[v].append(u)

        @functools.cache
        def must_after_default(item) -> bool:
            return (item in out_neighbors[default]
                    or any(must_after_default(x) for x in in_neighbors[item]))

        # 若不直接或间接地指定 item 位于 default 之后，则默认地将 item 置于 default 之前
        for item in items:
            if item != default and not must_after_default(item):
                orders.append((item, default))
    return cast(list[T], topological_sort(items, orders))
