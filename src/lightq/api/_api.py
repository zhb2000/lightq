import asyncio
import json
import urllib.parse
import typing
from collections import deque
from typing import Any, AsyncIterator, cast

import websockets.client
import websockets.exceptions

from .. import entities
from ..entities import Message, Event, SyncMessage, UnsupportedEntity
from ..exceptions import MiraiApiException
from ..logging import logger
from .._commons import AutoIncrement
from ._api_mixin import ApiMixin


class DataQueue:
    def __init__(self):
        self.__queue: deque[dict[str, Any]] = deque()
        self.__consumers: deque[asyncio.Future[dict[str, Any]]] = deque()

    async def pop(self) -> dict[str, Any]:
        if len(self.__queue) > 0:
            return self.__queue.popleft()
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        self.__consumers.append(future)

        def remove_future(_):
            # the future may not be in the queue because the `clear` method may have called
            if future in self.__consumers:
                self.__consumers.remove(future)

        future.add_done_callback(remove_future)
        return await future

    def push(self, data: dict[str, Any]):
        if len(self.__consumers) > 0:
            self.__consumers[0].set_result(data)
        else:
            self.__queue.append(data)

    def set_exceptions(self, exception: BaseException):
        for future in self.__consumers:
            if not future.done():
                future.set_exception(exception)

    def clear(self):
        self.__queue.clear()
        # If the future is already done or canceled, future.cancel() will do nothing.
        for future in self.__consumers:
            future.cancel()
        self.__consumers.clear()


class ResponseDict:
    def __init__(self):
        self.__responses: dict[str, dict[str, Any]] = {}  # sync-id => response-data
        self.__consumers: dict[str, asyncio.Future[dict[str, Any]]] = {}  # sync-id => future

    async def get(self, sync_id: str) -> dict[str, Any]:
        if sync_id in self.__responses:
            return self.__responses.pop(sync_id)
        future: asyncio.Future[dict[str, Any]] = asyncio.Future()
        if sync_id in self.__consumers:
            raise KeyError(f'there is already a future waiting for response with sync_id: {sync_id}')
        self.__consumers[sync_id] = future
        # the future may not be in the dict because the `clear` method may have called
        future.add_done_callback(lambda _: self.__consumers.pop(sync_id, None))
        return await future

    def put(self, sync_id: str, response: dict[str, Any]):
        if sync_id in self.__consumers:
            self.__consumers[sync_id].set_result(response)
        else:
            self.__responses[sync_id] = response

    def set_exceptions(self, exception: BaseException):
        for future in self.__consumers.values():
            if not future.done():
                future.set_exception(exception)

    def clear(self):
        self.__responses.clear()
        for future in self.__consumers.values():
            future.cancel()
        self.__consumers.clear()


class MiraiApi(ApiMixin):
    def __init__(
        self,
        bot_id: int,
        verify_key: str,
        base_url: str = 'ws://localhost:8080',
        reserved_sync_id: str = '-1'
    ):
        self.bot_id = bot_id
        self.verify_key = verify_key
        self.base_url = base_url
        self.reserved_sync_id = reserved_sync_id
        self.__ws: websockets.client.WebSocketClientProtocol | None = None
        self.__session_key: str | None = None
        self.__queue = DataQueue()
        self.__responses = ResponseDict()
        self.__working_task: asyncio.Task[None] | None = None
        self.__increment_id = AutoIncrement(max_value=int(1e8))

    @property
    def session_key(self) -> str | None: return self.__session_key

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Mirai-api-http 传入格式：

        ```json
        {
            "syncId": 123, // 消息同步的字段
            "command": "sendFriendMessage", // 命令字
            "subCommand": null, // 子命令字, 可空
            "content": {} // 命令的数据对象, 与通用接口定义相同
        }
        ```

        JSON 的 `syncId` 字段由 `send` 方法自动生成，无需传入。

        :returns: 若状态码为 0 则将响应的 JSON 返回
        :raises:
            MiraiApiException: 若状态码非 0 则抛出对应的异常
            websockets.exception.WebSocketException: WebSocket 连接被关闭或出错时抛出
        """
        await self.connect()
        if typing.TYPE_CHECKING:
            assert self.__ws is not None
        sync_id = self.__increment_id.get()
        data['syncId'] = sync_id
        logger.info(f'websocket send: {data}')
        await self.__ws.send(json.dumps(data))
        # 响应结果的 syncId 为字符串而非数字
        response = await self.__responses.get(str(sync_id))
        response = cast(dict[str, Any], response['data'])
        if 'code' not in response:  # 有的响应不含 code 字段
            return response
        if response['code'] == 0:
            return response
        else:
            raise MiraiApiException.from_response(response)

    async def recv(self) -> Message | Event | SyncMessage | UnsupportedEntity:
        """
        Mirai-api-http 推送格式：

        ```json
        {
            "syncId": "123", // 消息同步的字段
            "data": {} // 推送消息内容, 与通用接口定义相同
        }
        ```

        本方法会返回 JSON 的 `data` 部分。

        :raises websockets.exception.WebSocketException: WebSocket 连接被关闭或出错时抛出
        """
        await self.connect()
        data = await self.__queue.pop()
        data = cast(dict[str, Any], data['data'])
        if data['type'] in entities.MESSAGE_CLASSES:
            return Message.from_json(data)
        elif data['type'] in entities.EVENT_CLASSES:
            return Event.from_json(data)
        elif data['type'] in entities.SYNC_MESSAGE_CLASSES:
            return SyncMessage.from_json(data)
        else:
            return UnsupportedEntity(data)

    async def __working_method(self):
        if typing.TYPE_CHECKING:
            assert self.__ws is not None
        try:
            while True:
                data = cast(dict[str, Any], json.loads(await self.__ws.recv()))
                logger.info(f'websocket recv: {data}')
                sync_id: str = data['syncId']
                if sync_id == '':  # first message after connected
                    self.__session_key = data['data']['session']
                elif sync_id == self.reserved_sync_id:  # 他人发送的消息（并非响应结果）
                    self.__queue.push(data)
                else:  # 响应结果
                    self.__responses.put(sync_id, data)
        except websockets.exceptions.WebSocketException as exception:
            self.__queue.set_exceptions(exception)
            self.__responses.set_exceptions(exception)
        finally:
            self.__queue.clear()
            self.__responses.clear()
            self.__session_key = None
            self.__increment_id.reset()
            ws = self.__ws
            self.__ws = None
            await ws.close()  # the close method is idempotent

    async def connect(self):
        """与 mirai-api-http 建立连接。如果连接已经建立，则什么也不做。"""
        if self.__ws is not None:
            return
        encoded_key = urllib.parse.quote_plus(self.verify_key)
        self.__ws = await websockets.client.connect(
            urllib.parse.urljoin(
                self.base_url,
                f'/all?verifyKey={encoded_key}&qq={self.bot_id}'
            )
        )

        def remove_working_task(task):
            self.__working_task = None

        self.__working_task = asyncio.create_task(self.__working_method())
        self.__working_task.add_done_callback(remove_working_task)

    async def close(self):
        """断开与 mirai-api-http 的连接。如果连接已经断开，则什么也不做。"""
        if self.__ws is None:
            return
        await self.__ws.close()
        if typing.TYPE_CHECKING:
            assert self.__working_task is not None
        await self.__working_task  # wait for the working task to finish

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def __aiter__(self) -> AsyncIterator[Message | Event | SyncMessage | UnsupportedEntity]:
        async def generator():
            while True:
                try:
                    yield await self.recv()
                except websockets.exceptions.ConnectionClosedOK:
                    break

        return aiter(generator())

    async def send_command(
        self,
        command: str,
        content: dict[str, Any] | None = None,
        sub_command: str | None = None
    ) -> dict[str, Any]:
        return await self.send({
            'command': command,
            'content': content if content is not None else {},
            'subCommand': sub_command
        })

    __send_command__ = send_command
