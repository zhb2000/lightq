import unittest
import json

from lightq import entities
from lightq.entities import SyncMessage


class SyncMessageSerializeTest(unittest.TestCase):
    def test_friend_sync_message(self):
        j = json.loads('''
        {
            "type": "FriendSyncMessage",
            "subject": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }''')
        obj = SyncMessage.from_json(j)
        self.assertIsInstance(obj, entities.FriendSyncMessage)
        self.assertDictEqual(j, obj.to_json())

    def test_group_sync_message(self):
        j = json.loads('''
        {
            "type": "GroupSyncMessage",
            "subject": {
              "id": 321,
              "name": "",
              "permission": "MEMBER"
            },
            "messageChain": []
        }''')
        obj = SyncMessage.from_json(j)
        self.assertIsInstance(obj, entities.GroupSyncMessage)
        self.assertDictEqual(j, obj.to_json())

    def test_temp_sync_message(self):
        j = json.loads('''
        {
            "type": "TempSyncMessage",
            "subject": {
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
        obj = SyncMessage.from_json(j)
        self.assertIsInstance(obj, entities.TempSyncMessage)
        self.assertDictEqual(j, obj.to_json())

    def test_stranger_sync_message(self):
        j = json.loads('''
        {
            "type": "StrangerSyncMessage",
            "subject": {
                "id": 123,
                "nickname": "",
                "remark": ""
            },
            "messageChain": []
        }''')
        obj = SyncMessage.from_json(j)
        self.assertIsInstance(obj, entities.StrangerSyncMessage)
        self.assertDictEqual(j, obj.to_json())


if __name__ == '__main__':
    unittest.main()
