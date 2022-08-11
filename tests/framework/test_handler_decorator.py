import unittest

from lightq import entities
from lightq import message_handler, event_handler, exception_handler


class HandlerDecoratorTest(unittest.TestCase):
    def test_message_handler_message(self):
        def make_handler():
            @message_handler(entities.Message)
            def handler():
                pass

            return handler

        self.assertRaises(TypeError, make_handler)

    def test_event_handler_event(self):
        def make_handler():
            @event_handler(entities.Event)
            def handler():
                pass

            return handler

        self.assertRaises(TypeError, make_handler)

    def test_exception_handler_exception(self):
        def make_handler():
            @exception_handler(Exception)
            def handler():
                pass

            return handler

        make_handler()
