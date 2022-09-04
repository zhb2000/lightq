import unittest
from typing import cast

from lightq import message_handler, exception_handler, resolve, RecvContext, ExceptionContext, Bot
from lightq.entities import FriendMessage, MessageChain, Plain


class ParamResolveTest(unittest.IsolatedAsyncioTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = Bot(0, '')

    async def test_type_based_resolver(self):
        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))

        @message_handler(FriendMessage)
        def handler(message: FriendMessage, message_chain: MessageChain, bot: Bot, ctx: RecvContext):
            self.assertIsInstance(message, FriendMessage)
            self.assertIsInstance(message_chain, MessageChain)
            self.assertIsInstance(bot, Bot)
            self.assertIsInstance(ctx, RecvContext)
            self.assertEqual(context, ctx)

        await handler.handle(context)

    async def test_function_based_resolver_named(self):
        def extract_text(ctx: RecvContext) -> str:
            return next(e.text for e in cast(FriendMessage, ctx.data).message_chain if isinstance(e, Plain))

        @resolve(text=extract_text)
        @message_handler(FriendMessage)
        def handler(text: str):
            self.assertEqual('lalala', text)

        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": [
                {
                    "type": "Plain",
                    "text": "lalala"
                }
            ]
        }))
        await handler.handle(context)

    async def test_function_based_resolver_unnamed(self):
        def text(ctx: RecvContext) -> str:
            return next(e.text for e in cast(FriendMessage, ctx.data).message_chain if isinstance(e, Plain))

        @resolve(text)
        @message_handler(FriendMessage)
        def handler(text: str):
            self.assertEqual('lalala', text)

        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": [
                {
                    "type": "Plain",
                    "text": "lalala"
                }
            ]
        }))
        await handler.handle(context)

    async def test_type_and_function_based_resolver(self):
        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": [
                {
                    "type": "Plain",
                    "text": "lalala"
                }
            ]
        }))

        def text(ctx: RecvContext) -> str:
            return next(e.text for e in cast(FriendMessage, ctx.data).message_chain if isinstance(e, Plain))

        @resolve(text, s=text, bot=Bot.from_recv_context)
        @message_handler(FriendMessage)
        def handler(
            text: str,
            s: str,
            message: FriendMessage,
            message_chain: MessageChain,
            bot: Bot,
            ctx: RecvContext
        ):
            self.assertEqual('lalala', text)
            self.assertEqual('lalala', s)
            self.assertIsInstance(message, FriendMessage)
            self.assertIsInstance(message_chain, MessageChain)
            self.assertIsInstance(bot, Bot)
            self.assertIsInstance(ctx, RecvContext)
            self.assertEqual(context, ctx)

        await handler.handle(context)

    async def test_exception_type_resolve(self):
        context = ExceptionContext(
            ValueError(),
            RecvContext(self.bot, FriendMessage.from_json({
                "type": "FriendMessage",
                "sender": {
                    "id": 123,
                    "nickname": "",
                    "remark": ""
                },
                "messageChain": []
            })),
            None
        )

        @exception_handler(ValueError)
        def handler(exception: ValueError):
            self.assertIsInstance(exception, ValueError)

        await handler.handle(context)


if __name__ == '__main__':
    unittest.main()
