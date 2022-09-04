import unittest
import json

from lightq import entities
from lightq.entities import Message


class MessageSerializeTest(unittest.TestCase):
    def test_friend_message(self):
        j = json.loads('''
        {
            "type": "FriendMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }''')
        obj = Message.from_json(j)
        self.assertIsInstance(obj, entities.FriendMessage)
        self.assertDictEqual(j, obj.to_json())

    def test_group_message(self):
        j = json.loads('''
        {
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
        }''')
        obj = Message.from_json(j)
        self.assertIsInstance(obj, entities.GroupMessage)
        self.assertDictEqual(j, obj.to_json())

    def test_temp_message(self):
        j = json.loads('''
        {
            "type": "TempMessage",
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
        }''')
        obj = Message.from_json(j)
        self.assertIsInstance(obj, entities.TempMessage)
        self.assertDictEqual(j, obj.to_json())

    def test_stranger_message(self):
        j = json.loads('''
        {
            "type": "StrangerMessage",
            "sender": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }''')
        obj = Message.from_json(j)
        self.assertIsInstance(obj, entities.StrangerMessage)
        self.assertDictEqual(j, obj.to_json())

    def test_other_client_message(self):
        j = json.loads('''
        {
            "type": "OtherClientMessage",
            "sender": {
                "id": 123,
                "platform": "MOBILE"
            },
            "messageChain": []
        }''')
        obj = Message.from_json(j)
        self.assertIsInstance(obj, entities.OtherClientMessage)
        self.assertDictEqual(j, obj.to_json())


if __name__ == '__main__':
    unittest.main()
