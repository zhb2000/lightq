import unittest

from lightq import exception_handler, Bot, RecvContext, ExceptionContext
from lightq.entities import FriendMessage
from lightq.framework._router import ExceptionTypeRouter


class MyException(Exception):
    pass


class MessageRouterTest(unittest.IsolatedAsyncioTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = ExceptionTypeRouter()
        self.recv_context = RecvContext(
            Bot(0, ''),
            FriendMessage.from_json({
                "type": "FriendMessage",
                "sender": {
                    "id": 123,
                    "nickname": "",
                    "remark": ""
                },
                "messageChain": []
            }))

    async def test_exact_type(self):
        @exception_handler(Exception)
        def handler_exception():
            pass

        @exception_handler(MyException)
        def handler_my_exception():
            pass

        self.router.build([handler_exception, handler_my_exception])
        context = ExceptionContext(MyException(), self.recv_context, None)
        self.assertIs(await self.router.route(context), handler_my_exception)

    async def test_base_type(self):
        @exception_handler(Exception)
        def handler_exception():
            pass

        @exception_handler(MyException, filters=lambda _: False)
        def handler_my_exception():
            pass

        self.router.build([handler_exception, handler_my_exception])
        context = ExceptionContext(MyException(), self.recv_context, None)
        self.assertIs(await self.router.route(context), handler_exception)

    async def test_multi_type(self):
        @exception_handler(ValueError, MyException)
        def handler():
            pass

        self.router.build([handler])

        exception = ValueError()
        context = ExceptionContext(exception, self.recv_context, None)
        h = await self.router.route(context)
        self.assertIs(h, handler)
        await h.handle(context)

        exception = MyException()
        context = ExceptionContext(exception, self.recv_context, None)
        h = await self.router.route(context)
        self.assertIs(h, handler)
        await h.handle(context)

        exception = KeyError()
        context = ExceptionContext(exception, self.recv_context, None)
        self.assertIsNone(await self.router.route(context))


if __name__ == '__main__':
    unittest.main()
