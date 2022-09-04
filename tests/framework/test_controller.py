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

    def test_controller_handlers(self):
        self.assertSetEqual(
            {
                self.controller.public_message_handler,
                self.controller.public_event_handler,
                self.controller.public_exception_handler
            },
            set(self.controller.handlers)
        )

    def test_handler_property_runtime_check(self):
        def action():
            class Ctrl(Controller):
                @handler_property
                def wrong_type_property(self):
                    return 0

            _ = list(Ctrl().handlers)

        self.assertRaises(Exception, action)


if __name__ == '__main__':
    unittest.main()
