import unittest
import asyncio

from lightq import Controller, message_handler, resolve, resolvers, MessageHandler, Bot, RecvContext
from lightq.entities import FriendMessage


class HandlerMethodTest(unittest.IsolatedAsyncioTestCase):
    def test_descriptor(self):
        class MyController(Controller):
            @message_handler(FriendMessage)
            def handler_method(self):
                pass

        obj = MyController()
        self.assertIsInstance(obj.handler_method, MessageHandler)
        self.assertIsNot(obj.handler_method, MyController.handler_method)
        # cache the same handler for the same instance
        self.assertIs(obj.handler_method, obj.handler_method)
        obj2 = MyController()
        # different handlers for different instances
        self.assertIsNot(obj.handler_method, obj2.handler_method)

    async def test_call_method(self):
        outer_self = self

        class MyController(Controller):
            def __init__(self, status: int):
                self.status = status

            @resolve(resolvers.sender_id)
            @message_handler(FriendMessage)
            def handler_method(self, message: FriendMessage, sender_id: int) -> str:
                # test accessing self status
                outer_self.assertEqual(1, self.status)
                # test type-based resolver
                outer_self.assertIsInstance(message, FriendMessage)
                # test function-based resolver
                outer_self.assertEqual(233, sender_id)
                return 'response'

        obj = MyController(1)
        context = RecvContext(Bot(0, ''), FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 233,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        response = await obj.handler_method.handle(context)
        self.assertEqual('response', str(response))

    def test_before_after(self):
        @message_handler(FriendMessage)
        def handler_function():
            pass

        class MyController(Controller):
            def __init__(self) -> None:
                self.handler_method1.before = [self.handler_method2, handler_function]

            @message_handler(FriendMessage)
            def handler_method1(self):
                pass

            @message_handler(FriendMessage, after=[handler_method1, handler_function])
            def handler_method2(self):
                pass

        obj = MyController()
        self.assertListEqual([obj.handler_method2, handler_function], obj.handler_method1.before)
        self.assertListEqual([obj.handler_method1, handler_function], obj.handler_method2.after)

    def test_inherited_handler_method(self):
        class Base(Controller):
            @message_handler(FriendMessage)
            def base_handler_method(self):
                pass

        class Derived(Base):
            @message_handler(FriendMessage, after=Base.base_handler_method)
            def derived_handler_method(self):
                pass

        obj = Derived()
        self.assertIsNot(obj.base_handler_method, Base.base_handler_method)
        self.assertIs(obj.base_handler_method, obj.base_handler_method)
        self.assertListEqual([obj.base_handler_method], obj.derived_handler_method.after)
        obj2 = Derived()
        self.assertIsNot(obj.base_handler_method, obj2.base_handler_method)

    async def test_filter_resolver_method(self):
        outer_self = self

        class MyController(Controller):
            def __init__(self, status: str):
                self.status = status

            def filter_method(self, context: RecvContext) -> bool:
                return self.status == 'ok'

            def resolver_method(self, context: RecvContext) -> str:
                return self.status

            @resolve(resolve_result=resolver_method)
            @message_handler(FriendMessage, filters=filter_method)
            def handler_method(self, resolve_result: str) -> str:
                outer_self.assertEqual(self.status, resolve_result)
                return 'response'

        obj = MyController('not ok')
        context = RecvContext(Bot(0, ''), FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 233,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertFalse(await obj.handler_method.can_handle(context))
        obj.status = 'ok'
        self.assertTrue(await obj.handler_method.can_handle(context))
        response = await obj.handler_method.handle(context)
        self.assertEqual('response', str(response))
        obj2 = MyController('obj 2')
        self.assertNotEqual(obj.handler_method.filters, obj2.handler_method.filters)
        self.assertNotEqual(obj.handler_method.resolvers, obj2.handler_method.resolvers)

    async def test_inherited_filter_resolver_method(self):
        outer_self = self

        class Base(Controller):
            def __init__(self, status: str) -> None:
                self.status = status
            
            def filter_method(self, context: RecvContext) -> bool:
                return self.status == 'ok'

            def resolver_method(self, context: RecvContext) -> str:
                return self.status

        class Derived(Base):
            def __init__(self, status: str) -> None:
                super().__init__(status)

            @resolve(resolve_result=Base.resolver_method)
            @message_handler(FriendMessage, filters=Base.filter_method)
            def handler_method(self, resolve_result: str) -> str:
                outer_self.assertEqual(self.status, resolve_result)
                return 'response'

        obj = Derived('not ok')
        context = RecvContext(Bot(0, ''), FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 233,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertFalse(await obj.handler_method.can_handle(context))
        obj.status = 'ok'
        self.assertTrue(await obj.handler_method.can_handle(context))
        response = await obj.handler_method.handle(context)
        self.assertEqual('response', str(response))
        obj2 = Derived('obj2')
        self.assertNotEqual(obj.handler_method.filters, obj2.handler_method.filters)
        self.assertNotEqual(obj.handler_method.resolvers, obj2.handler_method.resolvers)

    async def test_different_instance(self):
        outer_self = self

        class MyController(Controller):
            def __init__(self, status: int):
                self.status = status

            def filter_method(self, context: RecvContext) -> bool:
                return self.status == 1

            def resolver_method(self, context: RecvContext) -> int:
                return self.status + 100

            @resolve(resolve_result=resolver_method)
            @message_handler(FriendMessage, filters=filter_method)
            def handler_method(self, resolve_result: int) -> str:
                outer_self.assertEqual(self.status + 100, resolve_result)
                return str(self.status)

        obj1 = MyController(1)
        obj2 = MyController(2)
        context = RecvContext(Bot(0, ''), FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 233,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertTrue(await obj1.handler_method.can_handle(context))
        self.assertFalse(await obj2.handler_method.can_handle(context))
        self.assertEqual('1', str(await obj1.handler_method.handle(context)))
        self.assertEqual('2', str(await obj2.handler_method.handle(context)))

    async def test_async_method(self):
        outer_self = self

        class MyController(Controller):
            def __init__(self, status: int):
                self.status = status

            async def filter_method(self, context: RecvContext) -> bool:
                await asyncio.sleep(0)
                return self.status == 1

            async def resolver_method(self, context: RecvContext) -> int:
                await asyncio.sleep(0)
                return self.status + 100

            @resolve(resolve_result=resolver_method)
            @message_handler(FriendMessage, filters=filter_method)
            async def handler_method(self, resolve_result: int) -> str:
                await asyncio.sleep(0)
                outer_self.assertEqual(self.status + 100, resolve_result)
                return 'response'

        obj = MyController(1)
        context = RecvContext(Bot(0, ''), FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 233,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertTrue(await obj.handler_method.can_handle(context))
        obj.status = -1
        self.assertFalse(await obj.handler_method.can_handle(context))
        obj.status = 1
        response = await obj.handler_method.handle(context)
        self.assertEqual('response', str(response))
        obj2 = MyController(1)
        self.assertNotEqual(obj.handler_method.filters, obj2.handler_method.filters)
        self.assertNotEqual(obj.handler_method.resolvers, obj2.handler_method.resolvers)

    async def test_other_class_method_failed(self):
        with self.assertRaises(TypeError):
            class OtherController(Controller):
                @message_handler(FriendMessage)
                def other_class_method(self):
                    pass

            class MyController(Controller):
                @message_handler(FriendMessage, before=OtherController.other_class_method)
                def handler_method(self):
                    pass

            obj = MyController()
            obj.handler_method  # trigger __get__ on descriptor 'handler_method'


if __name__ == '__main__':
    unittest.main()
