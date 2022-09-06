import unittest

from lightq import Controller, handler_property, message_handler, event_handler, exception_handler
from lightq.entities import FriendMessage, FriendRecallEvent


class MyController(Controller):
    @handler_property
    def public_message_handler(self):
        @message_handler(FriendMessage)
        def handler():
            pass

        return handler

    @handler_property
    def public_event_handler(self):
        @event_handler(FriendRecallEvent)
        def handler():
            pass

        return handler

    @handler_property
    def public_exception_handler(self):
        @exception_handler(Exception)
        def handler():
            pass

        return handler

    @handler_property
    def _protected_message_handler(self):
        @message_handler(FriendMessage)
        def handler():
            pass

        return handler

    @handler_property
    def __private_message_handler(self):
        @message_handler(FriendMessage)
        def handler():
            pass

        return handler

    @property
    def common_property_handler(self):
        @message_handler(FriendMessage)
        def handler():
            pass

        return handler

    @property
    def dont_get_this_property(self):
        if str(0) == '0':
            assert False
        return 0


class ControllerTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = MyController()

    def test_property_cache(self):
        self.assertIs(self.controller.public_message_handler, self.controller.public_message_handler)
        self.assertIs(self.controller.public_event_handler, self.controller.public_event_handler)
        self.assertIs(self.controller.public_exception_handler, self.controller.public_exception_handler)

    def test_different_instance_property(self):
        a = MyController()
        b = MyController()
        self.assertIsNot(a.public_message_handler, b.public_message_handler)

    def test_controller_handlers(self):
        self.assertCountEqual([
            self.controller.public_message_handler,
            self.controller.public_event_handler,
            self.controller.public_exception_handler
        ], self.controller.handlers)


if __name__ == '__main__':
    unittest.main()
