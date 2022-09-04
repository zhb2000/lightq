import unittest

from lightq import message_handler, Bot, RecvContext
from lightq.entities import FriendMessage, GroupMessage, Message
from lightq.framework._router import MessageTypeRouter


class MessageRouterTest(unittest.IsolatedAsyncioTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = MessageTypeRouter()
        self.bot = Bot(0, '')

    async def test_type_and_condition(self):
        @message_handler(FriendMessage, filters=lambda ctx: False)
        def handler1():
            pass

        @message_handler(FriendMessage)
        def handler2():
            pass

        @message_handler(FriendMessage)
        def handler3():
            pass

        self.router.build([handler1, handler2, handler3])
        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertIs(await self.router.route(context), handler2)

    async def test_type(self):
        @message_handler(GroupMessage)
        def group_message_handler():
            pass

        @message_handler(FriendMessage)
        def friend_message_handler():
            pass

        self.router.build([group_message_handler, friend_message_handler])
        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertIs(await self.router.route(context), friend_message_handler)

    async def test_base_type(self):
        @message_handler(Message)
        def base_message_handler():
            pass

        @message_handler(FriendMessage)
        def friend_message_handler():
            pass

        self.router.build([base_message_handler, friend_message_handler])
        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertIs(await self.router.route(context), friend_message_handler)
        context = RecvContext(self.bot, GroupMessage.from_json({
            "type": "GroupMessage",
            "sender": {
                "id": 123,
                "memberName": "",
                "specialTitle": "",
                "permission": "OWNER",
                "joinTimestamp": 0,
                "lastSpeakTimestamp": 0,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 321,
                    "name": "",
                    "permission": "MEMBER"
                }
            },
            "messageChain": []
        }))
        self.assertIs(await self.router.route(context), base_message_handler)

    async def test_return_none(self):
        @message_handler(GroupMessage)
        def group_message_handler():
            pass

        @message_handler(FriendMessage, filters=lambda _: False)
        def friend_message_handler():
            pass

        self.router.build([group_message_handler, friend_message_handler])
        context = RecvContext(self.bot, FriendMessage.from_json({
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }))
        self.assertIsNone(await self.router.route(context))


if __name__ == '__main__':
    unittest.main()
