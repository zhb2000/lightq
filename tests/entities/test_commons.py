import unittest
import json

from lightq import entities


class CommonsEntitySerializeTest(unittest.TestCase):
    def test_friend(self):
        j = json.loads('''
        {
            "id": 123,
            "nickname": "nickname",
            "remark": "remark"
        }''')
        obj = entities.Friend.from_json(j)
        self.assertIsInstance(obj, entities.Friend)
        self.assertDictEqual(j, obj.to_json())

    def test_group(self):
        j = json.loads('''
        {
            "id": 321,
            "name": "name",
            "permission": "MEMBER"
        }''')
        obj = entities.Group.from_json(j)
        self.assertIsInstance(obj, entities.Group)
        self.assertDictEqual(j, obj.to_json())

    def test_member(self):
        j = json.loads('''
        {
            "id": 123,
            "memberName": "memberName",
            "specialTitle": "specialTitle",
            "permission": "OWNER",
            "joinTimestamp": 0,
            "lastSpeakTimestamp": 0,
            "muteTimeRemaining": 0,
            "group": {
                "id": 321,
                "name": "name",
                "permission": "MEMBER"
            }
        }''')
        obj = entities.Member.from_json(j)
        self.assertIsInstance(obj, entities.Member)
        self.assertDictEqual(j, obj.to_json())

    def test_client(self):
        j = json.loads('''
        {
            "id": 123,
            "platform": "MOBILE"
        }''')
        obj = entities.Client.from_json(j)
        self.assertIsInstance(obj, entities.Client)
        self.assertDictEqual(j, obj.to_json())

    def test_profile(self):
        j = json.loads('''
        {
            "nickname":"nickname",
            "email":"email",
            "age":18,
            "level":1,
            "sign":"mirai",
            "sex":"UNKNOWN"
        }''')
        obj = entities.Profile.from_json(j)
        self.assertIsInstance(obj, entities.Profile)
        self.assertDictEqual(j, obj.to_json())

    def test_group_config(self):
        j = json.loads('''
        {
            "name":"群名称",
            "announcement":"群公告",
            "confessTalk":true,
            "allowMemberInvite":true,
            "autoApprove":true,
            "anonymousChat":true
        }''')
        obj = entities.GroupConfig.from_json(j)
        self.assertIsInstance(obj, entities.GroupConfig)
        self.assertDictEqual(j, obj.to_json())

    def test_announcement(self):
        j = json.loads('''
        {
            "group": {
                "id": 123456789,
                "name": "group name",
                "permission": "ADMINISTRATOR"
            },
            "content": "群公告内容",
            "senderId": 987654321,
            "fid": "公告唯一id",
            "allConfirmed": false,
            "confirmedMembersCount": 0,
            "publicationTime": 1645085843
        }''')
        obj = entities.Announcement.from_json(j)
        self.assertIsInstance(obj, entities.Announcement)
        self.assertDictEqual(j, obj.to_json())


if __name__ == '__main__':
    unittest.main()
