import unittest

from lightq import Controller, handler_property, message_handler, event_handler, exception_handler
from lightq.entities import Message, Event


class ControllerHandlerTest(unittest.TestCase):
    def test_message_event_exception_handlers(self):
        class MyController(Controller):
            @message_handler(Message)
            def message_handler_method(self): pass

            @event_handler(Event)
            def event_handler_method(self): pass

            @exception_handler(Exception)
            def exception_handler_method(self): pass

            @handler_property
            def message_handler_property(self):
                @message_handler(Message)
                def handler(): pass

                return handler

            @handler_property
            def event_handler_property(self):
                @event_handler(Event)
                def handler(): pass

                return handler

            @handler_property
            def exception_handler_property(self):
                @exception_handler(Exception)
                def handler(): pass

                return handler

        obj = MyController()
        message_handlers = [obj.message_handler_method, obj.message_handler_property]
        event_handlers = [obj.event_handler_method, obj.event_handler_property]
        exception_handlers = [obj.exception_handler_method, obj.exception_handler_property]
        self.assertCountEqual(message_handlers, obj.message_handlers())
        self.assertCountEqual(event_handlers, obj.event_handlers())
        self.assertCountEqual(exception_handlers, obj.exception_handlers())
        self.assertCountEqual([*message_handlers, *event_handlers, *exception_handlers], obj.handlers())

    def test_class_inherit(self):
        class Base(Controller):
            @message_handler(Message)
            def base_method(self): pass

            @handler_property
            def base_property(self):
                @message_handler(Message)
                def handler(): pass

                return handler

        class Derived(Base):
            @message_handler(Message)
            def derived_method(self): pass

            @handler_property
            def derived_property(self):
                @message_handler(Message)
                def handler(): pass

                return handler

        obj = Derived()
        self.assertCountEqual([
            obj.base_method,
            obj.base_property,
            obj.derived_method,
            obj.derived_property
        ], obj.handlers())

    def test_controller_handlers_getattr(self):
        outer_self = self

        class MyController(Controller):
            def __init__(self) -> None:
                @message_handler(Message)
                def handler(): pass
                self.instance = handler  # Don't get instance handlers

            @message_handler(Message)
            def public_method(self): pass

            @message_handler(Message)
            def _protected_method(self): pass

            @message_handler(Message)
            def __private_method(self): pass

            def trivial_method(self): pass

            @handler_property
            def public_property(self):
                @message_handler(Message)
                def handler(): pass

                return handler

            @handler_property
            def _protected_property(self):
                @message_handler(Message)
                def handler(): pass

                return handler

            @handler_property
            def __private_property(self):
                @message_handler(Message)
                def handler(): pass

                return handler

            # Don't get builtin properties, only get properties
            # decorated with `handler_property`
            @property
            def builtin_property(self):
                @message_handler(Message)
                def handler(): pass

                return handler

            @property
            def dont_get_this_property(self):
                outer_self.fail()

        obj = MyController()
        self.assertCountEqual([
            obj.public_method,
            obj.public_property
        ], obj.handlers())


if __name__ == '__main__':
    unittest.main()
