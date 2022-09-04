import unittest
import re
import typing

from lightq import entities, filters, RecvContext, ExceptionContext, Bot
from lightq.entities import FriendMessage, Friend, MessageChain
from lightq.decorators import (
    regex_match,
    regex_search,
    regex_fullmatch,
    message_handler,
    exception_handler,
    resolve
)


class RegexDecoratorTest(unittest.IsolatedAsyncioTestCase):
    @staticmethod
    def make_context(text: str):
        return RecvContext(
            Bot(0, ''),
            FriendMessage(
                Friend(0, '', ''),
                MessageChain([entities.Plain(text)])
            )
        )
        pass

    async def test_regex_match(self):
        @regex_match(r'(?P<first_name>\w+) (?P<last_name>\w+)')
        @message_handler(FriendMessage)
        def handler(first_name: str, last_name: str, match: re.Match):
            self.assertEqual('First', first_name)
            self.assertEqual('Last', last_name)
            self.assertIsInstance(match, re.Match)

        context = self.make_context('name')
        self.assertFalse(await handler.can_handle(context))

        context = self.make_context('First Last')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

        context = self.make_context(' First Last')
        self.assertFalse(await handler.can_handle(context))

        context = self.make_context('First Last ')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

    async def test_typing_match(self):
        @regex_match(r'(?P<first_name>\w+) (?P<last_name>\w+)')
        @message_handler(FriendMessage)
        def handler(match: typing.Match):
            self.assertEqual('First', match['first_name'])
            self.assertEqual('Last', match['last_name'])
            self.assertIsInstance(match, re.Match)

        context = self.make_context('First Last')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

    async def test_extractor(self):
        def extractor(chain: MessageChain) -> str:
            self.assertIsInstance(chain, MessageChain)
            self.assertEqual('First Last', str(chain))
            return 'custom extractor'

        @regex_match(r'(?P<first_name>\w+) (?P<last_name>\w+)', extractor=extractor)
        @message_handler(FriendMessage)
        def handler(first_name: str, last_name: str, match: re.Match):
            self.assertEqual('custom', first_name)
            self.assertEqual('extractor', last_name)
            self.assertIsInstance(match, re.Match)

        context = self.make_context('First Last')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

    async def test_regex_with_other_decorators(self):
        @resolve(param1=lambda ctx: 1)
        @regex_match(r'(?P<first_name>\w+) (?P<last_name>\w+)')
        @resolve(param3=lambda ctx: 'param3', param2=lambda ctx: 2)
        @message_handler(FriendMessage, filters=filters.is_at_user(233))
        def handler(
            match: re.Match,
            first_name: str,
            last_name: str,
            chain: MessageChain,
            param1: int,
            param2: int,
            param3: str
        ):
            self.assertIsInstance(match, re.Match)
            self.assertEqual('First', first_name)
            self.assertEqual('Last', last_name)
            self.assertIsInstance(chain, MessageChain)
            self.assertEqual(1, param1)
            self.assertEqual(2, param2)
            self.assertEqual('param3', param3)

        context = self.make_context('First Last')
        self.assertFalse(await handler.can_handle(context))

        context.data.message_chain.append(entities.At(233))
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

        context = self.make_context('name')
        self.assertFalse(await handler.can_handle(context))

    async def test_exception_context(self):
        @regex_match(r'(?P<first_name>\w+) (?P<last_name>\w+)')
        @exception_handler(ValueError)
        def handler(first_name: str, last_name: str, match: re.Match):
            self.assertEqual('First', first_name)
            self.assertEqual('Last', last_name)
            self.assertIsInstance(match, re.Match)

        context = ExceptionContext(ValueError(), self.make_context('name'), None)
        self.assertFalse(await handler.can_handle(context))

        context = ExceptionContext(ValueError(), self.make_context('First Last'), None)
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

    async def test_regex_search(self):
        @regex_search(r'(?P<first_name>\w+) (?P<last_name>\w+)')
        @message_handler(FriendMessage)
        def handler(first_name: str, last_name: str, match: re.Match):
            self.assertEqual('First', first_name)
            self.assertEqual('Last', last_name)
            self.assertIsInstance(match, re.Match)

        context = self.make_context('name')
        self.assertFalse(await handler.can_handle(context))

        context = self.make_context('First Last')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

        context = self.make_context(' First Last')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

        context = self.make_context('First Last ')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

    async def test_regex_fullmatch(self):
        @regex_fullmatch(r'(?P<first_name>\w+) (?P<last_name>\w+)')
        @message_handler(FriendMessage)
        def handler(first_name: str, last_name: str, match: re.Match):
            self.assertEqual('First', first_name)
            self.assertEqual('Last', last_name)
            self.assertIsInstance(match, re.Match)

        context = self.make_context('name')
        self.assertFalse(await handler.can_handle(context))

        context = self.make_context('First Last')
        self.assertTrue(await handler.can_handle(context))
        await handler.handle(context)

        context = self.make_context(' First Last')
        self.assertFalse(await handler.can_handle(context))

        context = self.make_context('First Last ')
        self.assertFalse(await handler.can_handle(context))


if __name__ == '__main__':
    unittest.main()
