import unittest
import json

from lightq import exceptions


class MiraiApiExceptionTest(unittest.TestCase):
    def test_mirai_api_exception_from(self):
        response = json.loads('''
        {
            "code": 1,
            "msg": "I am a message."
        }''')
        e = exceptions.MiraiApiException.from_response(response)
        self.assertIsInstance(e, exceptions.WrongVerifyKey)
        self.assertEqual(1, e.code)
        self.assertEqual('I am a message.', e.message)

    def test_concrete_exception_from(self):
        response = json.loads('''
        {
            "code": 1,
            "msg": "I am a message."
        }''')
        e = exceptions.WrongVerifyKey.from_response(response)
        self.assertIsInstance(e, exceptions.WrongVerifyKey)
        self.assertEqual(1, e.code)
        self.assertEqual('I am a message.', e.message)

    def test_wrong_concrete_exception_from(self):
        response = json.loads('''
        {
            "code": 1,
            "msg": "I am a message."
        }''')
        with self.assertRaises(Exception):
            exceptions.BotNotExist.from_response(response)

    def test_unsupported_api_exception_from(self):
        response = json.loads('''
        {
            "code": 500,
            "msg": "I am a message."
        }''')
        e = exceptions.MiraiApiException.from_response(response)
        self.assertIsInstance(e, exceptions.UnsupportedApiException)


if __name__ == '__main__':
    unittest.main()
