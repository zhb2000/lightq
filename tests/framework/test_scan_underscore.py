import unittest

from lightq import message_handler, event_handler, exception_handler, scan_handlers
from lightq.entities import FriendMessage, FriendRecallEvent


@message_handler(FriendMessage)
def public_message_handler(context):
    pass


@event_handler(FriendRecallEvent)
def public_event_handler(context):
    pass


@exception_handler(Exception)
def public_exception_handler(context):
    pass


@message_handler(FriendMessage)
def _message_handler(context):
    pass


@message_handler(FriendMessage)
def __message_handler(context):
    pass


class ScanUnderscoreTest(unittest.TestCase):
    def test_scan_underscore(self):
        self.assertSetEqual(
            {
                public_message_handler,
                public_event_handler,
                public_exception_handler
            },
            set(scan_handlers(__name__))
        )


if __name__ == '__main__':
    unittest.main()
