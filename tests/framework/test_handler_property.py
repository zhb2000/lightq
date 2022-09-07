import unittest

from lightq import Controller, handler_property, message_handler, event_handler, exception_handler
from lightq.entities import Message, Event


class HandlerPropertyTest(unittest.TestCase):
    def test_property_cache(self):
        class MyController(Controller):
            @handler_property
            def message_handler(self):
                @message_handler(Message)
                def handler(): pass

                return handler

            @handler_property
            def event_handler(self):
                @event_handler(Event)
                def handler(): pass

                return handler

            @handler_property
            def exception_handler(self):
                @exception_handler(Exception)
                def handler(): pass

                return handler

        obj = MyController()
        self.assertIs(obj.message_handler, obj.message_handler)
        self.assertIs(obj.event_handler, obj.event_handler)
        self.assertIs(obj.exception_handler, obj.exception_handler)

    def test_different_instance_property(self):
        class MyController(Controller):
            @handler_property
            def message_handler(self):
                @message_handler(Message)
                def handler(): pass

                return handler

        a = MyController()
        b = MyController()
        self.assertIsNot(a.message_handler, b.message_handler)


if __name__ == '__main__':
    unittest.main()
