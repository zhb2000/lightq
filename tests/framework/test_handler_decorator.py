import unittest

from lightq import (
    entities,
    message_handler,
    event_handler,
    exception_handler,
    MessageHandler,
    EventHandler,
    ExceptionHandler
)


class HandlerDecoratorTest(unittest.TestCase):
    def test_message_handler_message(self):
        @message_handler(entities.Message)
        def handler():
            pass

        self.assertIsInstance(handler, MessageHandler)

    def test_event_handler_event(self):
        @event_handler(entities.Event)
        def handler():
            pass

        self.assertIsInstance(handler, EventHandler)

    def test_exception_handler_exception(self):
        @exception_handler(Exception)
        def handler():
            pass

        self.assertIsInstance(handler, ExceptionHandler)


if __name__ == '__main__':
    unittest.main()
