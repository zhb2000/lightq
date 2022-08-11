import unittest
import json

from lightq import entities
from lightq.entities import Event


class EventSerializeTest(unittest.TestCase):
    # region Bot 自身事件
    def test_bot_online_event(self):
        j = json.loads('''
        {
            "type":"BotOnlineEvent",
            "qq":123456
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotOnlineEvent)
        self.assertEqual(obj.to_json(), j)

    def test_bot_offline_event_active(self):
        j = json.loads('''
        {
            "type":"BotOfflineEventActive",
            "qq":123456
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotOfflineEventActive)
        self.assertEqual(obj.to_json(), j)

    def test_bot_offline_event_force(self):
        j = json.loads('''
        {
            "type":"BotOfflineEventForce",
            "qq":123456
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotOfflineEventForce)
        self.assertEqual(obj.to_json(), j)

    def test_bot_offline_event_dropped(self):
        j = json.loads('''
        {
            "type":"BotOfflineEventDropped",
            "qq":123456
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotOfflineEventDropped)
        self.assertEqual(obj.to_json(), j)

    def test_bot_relogin_event(self):
        j = json.loads('''
        {
            "type":"BotReloginEvent",
            "qq":123456
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotReloginEvent)
        self.assertEqual(obj.to_json(), j)

    # endregion

    # region 好友事件
    def test_friend_input_status_changed_event(self):
        j = json.loads('''
        {
            "type": "FriendInputStatusChangedEvent",
            "friend": {
                "id": 123123,
                "nickname": "nick",
                "remark": "remark"
            }, 
            "inputting": true
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.FriendInputStatusChangedEvent)
        self.assertEqual(obj.to_json(), j)

    def test_friend_nick_changed_event(self):
        j = json.loads('''
        {
            "type": "FriendNickChangedEvent",
            "friend": {
                "id": 123123,
                "nickname": "nick",
                "remark": "remark"
            }, 
            "from": "origin nickname",
            "to": "new nickname"
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.FriendNickChangedEvent)
        self.assertEqual(obj.to_json(), j)

    # endregion

    # region 群事件
    def test_bot_group_permission_change_event(self):
        j = json.loads('''
        {
            "type": "BotGroupPermissionChangeEvent",
            "origin": "MEMBER",
            "current": "ADMINISTRATOR",
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "ADMINISTRATOR"
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotGroupPermissionChangeEvent)
        self.assertEqual(obj.to_json(), j)

    def test_bot_mute_event(self):
        j = json.loads('''
        {
            "type": "BotMuteEvent",
            "durationSeconds": 600,
            "operator": {
                "id": 123456789,
                "memberName": "我是管理员",
                "permission": "ADMINISTRATOR",
                "specialTitle":"群头衔",
                "joinTimestamp":12345678,
                "lastSpeakTimestamp":8765432,
                "muteTimeRemaining":0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotMuteEvent)
        self.assertEqual(obj.to_json(), j)

    def test_bot_unmute_event(self):
        j = json.loads('''
        {
            "type": "BotUnmuteEvent",
            "operator": {
                "id": 123456789,
                "memberName": "我是管理员",
                "permission": "ADMINISTRATOR",
                "specialTitle":"群头衔",
                "joinTimestamp":12345678,
                "lastSpeakTimestamp":8765432,
                "muteTimeRemaining":0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotUnmuteEvent)
        self.assertEqual(obj.to_json(), j)

    def test_bot_join_group_event(self):
        j = json.loads('''
        {
            "type": "BotJoinGroupEvent",
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "invitor": null
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotJoinGroupEvent)
        self.assertEqual(obj.to_json(), j)

    def test_bot_leave_event_active(self):
        j = json.loads('''
        {
            "type": "BotLeaveEventActive",
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotLeaveEventActive)
        self.assertEqual(obj.to_json(), j)

    def test_bot_leave_event_kick(self):
        j = json.loads('''
        {
            "type": "BotLeaveEventKick",
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "operator": null
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotLeaveEventKick)
        self.assertEqual(obj.to_json(), j)

    def test_bot_leave_event_disband(self):
        j = json.loads('''
        {
            "type": "BotLeaveEventDisband",
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "operator": null
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotLeaveEventDisband)
        self.assertEqual(obj.to_json(), j)

    def test_group_recall_event(self):
        j = json.loads('''
        {
            "type": "GroupRecallEvent",
            "authorId": 123456,
            "messageId": 123456789,
            "time": 1234679,
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "ADMINISTRATOR"
            },
            "operator": {
                "id": 123456789,
                "memberName": "我是管理员",
                "permission": "ADMINISTRATOR",
                "specialTitle": "群头衔",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.GroupRecallEvent)
        self.assertEqual(obj.to_json(), j)

    def test_friend_recall_event(self):
        j = json.loads('''
        {
            "type": "FriendRecallEvent",
            "authorId": 123456,
            "messageId": 123456789,
            "time": 1234679,
            "operator": 123456
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.FriendRecallEvent)
        self.assertEqual(obj.to_json(), j)

    def test_nudge_event(self):
        j = json.loads('''
        {
            "type": "NudgeEvent",
            "fromId": 123456,
            "subject": {
                "id": 123456,
                "kind": "Group"
            },
            "action": "戳了戳",
            "suffix": "的脸",
            "target": 123456
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.NudgeEvent)
        self.assertEqual(obj.to_json(), j)

    def test_group_name_change_event(self):
        j = json.loads('''
        {
            "type": "GroupNameChangeEvent",
            "origin": "miral technology",
            "current": "MIRAI TECHNOLOGY",
            "group": {
                "id": 123456789,
                "name": "MIRAI TECHNOLOGY",
                "permission": "MEMBER"
            },
            "operator": {
                "id": 123456,
                "memberName": "我是群主",
                "permission": "ADMINISTRATOR",
                "specialTitle": "群头衔",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "OWNER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.GroupNameChangeEvent)
        self.assertEqual(obj.to_json(), j)

    def test_group_entrance_announcement_change_event(self):
        j = json.loads('''
        {
            "type": "GroupEntranceAnnouncementChangeEvent",
            "origin": "abc",
            "current": "cba",
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "operator": {
                "id": 123456789,
                "memberName": "我是管理员",
                "permission": "ADMINISTRATOR",
                "specialTitle": "群头衔",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.GroupEntranceAnnouncementChangeEvent)
        self.assertEqual(obj.to_json(), j)

    def test_group_mute_all_event(self):
        j = json.loads('''
        {
            "type": "GroupMuteAllEvent",
            "origin": false,
            "current": true,
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "operator": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "OWNER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.GroupMuteAllEvent)
        self.assertEqual(obj.to_json(), j)

    def test_group_allow_anonymous_chat_event(self):
        j = json.loads('''
        {
            "type": "GroupAllowAnonymousChatEvent",
            "origin": false,
            "current": true,
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "operator": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "OWNER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.GroupAllowAnonymousChatEvent)
        self.assertEqual(obj.to_json(), j)

    def test_group_allow_confess_talk_event(self):
        j = json.loads('''
        {
            "type": "GroupAllowConfessTalkEvent",
            "origin": false,
            "current": true,
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "isByBot": false
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.GroupAllowConfessTalkEvent)
        self.assertEqual(obj.to_json(), j)

    def test_group_allow_member_invite_event(self):
        j = json.loads('''
        {
            "type": "GroupAllowMemberInviteEvent",
            "origin": false,
            "current": true,
            "group": {
                "id": 123456789,
                "name": "Miral Technology",
                "permission": "MEMBER"
            },
            "operator": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "OWNER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.GroupAllowMemberInviteEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_join_event(self):
        j = json.loads('''
        {
            "type": "MemberJoinEvent",
            "member": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            },
            "invitor": null
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberJoinEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_leave_event_kick(self):
        j = json.loads('''
        {
            "type": "MemberLeaveEventKick",
            "member": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            },
            "operator": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "OWNER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberLeaveEventKick)
        self.assertEqual(obj.to_json(), j)

    def test_member_leave_event_quit(self):
        j = json.loads('''
        {
            "type": "MemberLeaveEventQuit",
            "member": {
                "id": 123456789,
                "memberName": "我是被踢的",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberLeaveEventQuit)
        self.assertEqual(obj.to_json(), j)

    def test_member_card_change_event(self):
        j = json.loads('''
        {
            "type": "MemberCardChangeEvent",
            "origin": "origin name",
            "current": "我是被改名的",
            "member": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberCardChangeEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_special_title_change_event(self):
        j = json.loads('''
        {
            "type": "MemberSpecialTitleChangeEvent",
            "origin": "origin title",
            "current": "new title",
            "member": {
                "id": 123456789,
                "memberName": "我是被改头衔的",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberSpecialTitleChangeEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_permission_change_event(self):
        j = json.loads('''
        {
            "type": "MemberPermissionChangeEvent",
            "origin": "MEMBER",
            "current": "ADMINISTRATOR",
            "member": {
                "id": 123456789,
                "memberName": "我是被改权限的",
                "specialTitle": "群头衔",
                "permission": "ADMINISTRATOR",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 123456789,
                    "name": "Miral Technology",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberPermissionChangeEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_mute_event(self):
        j = json.loads('''
        {
            "type": "MemberMuteEvent",
            "durationSeconds": 600,
            "member": {
                "id": 1234567890,
                "memberName": "我是被取消禁言的",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            },
            "operator": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "OWNER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberMuteEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_unmute_event(self):
        j = json.loads('''
        {
            "type": "MemberUnmuteEvent",
            "member": {
                "id": 1234567890,
                "memberName": "我是被取消禁言的",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            },
            "operator": {
                "id": 1234567890,
                "memberName": "",
                "specialTitle": "群头衔",
                "permission": "OWNER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberUnmuteEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_honor_change_event(self):
        j = json.loads('''
        {
            "type": "MemberHonorChangeEvent",
            "member": {
                "id": 1234567890,
                "memberName": "我是被取消禁言的",
                "specialTitle": "群头衔",
                "permission": "MEMBER",
                "joinTimestamp": 12345678,
                "lastSpeakTimestamp": 8765432,
                "muteTimeRemaining": 0,
                "group": {
                    "id": 12345,
                    "name": "群名1",
                    "permission": "MEMBER"
                }
            },
            "action": "achieve",
            "honor": "龙王"
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberHonorChangeEvent)
        self.assertEqual(obj.to_json(), j)

    # endregion

    # region 申请事件
    def test_new_friend_request_event(self):
        j = json.loads('''
        {
            "type": "NewFriendRequestEvent",
            "eventId": 12345678,
            "fromId": 123456,
            "groupId": 654321,
            "nick": "Nick Name",
            "message": ""
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.NewFriendRequestEvent)
        self.assertEqual(obj.to_json(), j)

    def test_member_join_request_event(self):
        j = json.loads('''
        {
            "type": "MemberJoinRequestEvent",
            "eventId": 12345678,
            "fromId": 123456,
            "groupId": 654321,
            "groupName": "Group",
            "nick": "Nick Name",
            "message": ""
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.MemberJoinRequestEvent)
        self.assertEqual(obj.to_json(), j)

    def test_bot_invited_join_group_request_event(self):
        j = json.loads('''
        {
            "type": "BotInvitedJoinGroupRequestEvent",
            "eventId": 12345678,
            "fromId": 123456,
            "groupId": 654321,
            "groupName": "Group",
            "nick": "Nick Name",
            "message": ""
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.BotInvitedJoinGroupRequestEvent)
        self.assertEqual(obj.to_json(), j)

    # endregion

    # region 其他客户端事件
    def test_other_client_online_event(self):
        j = json.loads('''
        {
            "type": "OtherClientOnlineEvent",
            "client": {
                "id": 1,
                "platform": "WINDOWS"
            },
            "kind": 69899
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.OtherClientOnlineEvent)
        self.assertEqual(obj.to_json(), j)

    def test_other_client_offline_event(self):
        j = json.loads('''
        {
            "type": "OtherClientOfflineEvent",
            "client": {
                "id": 1,
                "platform": "WINDOWS"
            }
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.OtherClientOfflineEvent)
        self.assertEqual(obj.to_json(), j)

    # endregion

    # region 命令事件
    def test_command_execute_event(self):
        j = json.loads('''
        {
            "type": "CommandExecutedEvent",
            "name": "shutdown",
            "friend": null,
            "member": null,
            "args": [
                {
                    "type": "Plain",
                    "text": "myself"
                }
            ]
        }''')
        obj = Event.from_json(j)
        self.assertIsInstance(obj, entities.CommandExecutedEvent)
        self.assertEqual(obj.to_json(), j)
    # endregion
