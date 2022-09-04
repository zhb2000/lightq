import unittest
import json

from lightq import entities
from lightq.entities import MessageElement


class MessageElementSerializeTest(unittest.TestCase):
    def test_source(self):
        j = json.loads('''
        {
            "type": "Source",
            "id": 123456,
            "time": 123456
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Source)
        self.assertDictEqual(j, obj.to_json())

    def test_quote(self):
        j = json.loads('''
        {
            "type": "Quote",
            "id": 123456,
            "groupId": 123456789,
            "senderId": 987654321,
            "targetId": 9876543210,
            "origin": [
                { "type": "Plain", "text": "text" }
            ]
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Quote)
        self.assertDictEqual(j, obj.to_json())

    def test_at(self):
        j = json.loads('''
        {
            "type": "At",
            "target": 123456,
            "display": "@Mirai"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.At)
        self.assertDictEqual(j, obj.to_json())

    def test_at_all(self):
        j = json.loads('''
        {
            "type": "AtAll"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.AtAll)
        self.assertDictEqual(j, obj.to_json())

    def test_face(self):
        j = json.loads('''
        {
            "type": "Face",
            "faceId": 123,
            "name": "bu"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Face)
        self.assertDictEqual(j, obj.to_json())

    def test_plain(self):
        j = json.loads('''
        {
            "type": "Plain",
            "text": "Mirai牛逼"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Plain)
        self.assertDictEqual(j, obj.to_json())

    def test_Image(self):
        j = json.loads('''
        {
            "type": "Image",
            "imageId": "{01E9451B-70ED-EAE3-B37C-101F1EEBF5B5}.mirai",
            "url": "https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "path": null,
            "base64": null
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Image)
        self.assertDictEqual(j, obj.to_json())

    def test_flash_image(self):
        j = json.loads('''
        {
            "type": "FlashImage",
            "imageId": "{01E9451B-70ED-EAE3-B37C-101F1EEBF5B5}.mirai",
            "url": "https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "path": null,
            "base64": null
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.FlashImage)
        self.assertDictEqual(j, obj.to_json())

    def test_voice(self):
        j = json.loads('''
        {
            "type": "Voice",
            "voiceId": "23C477720A37FEB6A9EE4BCCF654014F.amr",
            "url": "https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "path": null,
            "base64": null,
            "length": 1024
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Voice)
        self.assertDictEqual(j, obj.to_json())

    def test_xml(self):
        j = json.loads('''
        {
            "type": "Xml",
            "xml": "XML"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Xml)
        self.assertDictEqual(j, obj.to_json())

    def test_json(self):
        j = json.loads('''
        {
            "type": "Json",
            "json": "{}"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Json)
        self.assertDictEqual(j, obj.to_json())

    def test_app(self):
        j = json.loads('''
        {
            "type": "App",
            "content": "<>"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.App)
        self.assertDictEqual(j, obj.to_json())

    def test_poke(self):
        j = json.loads('''{
            "type": "Poke",
            "name": "SixSixSix"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Poke)
        self.assertDictEqual(j, obj.to_json())

    def test_dice(self):
        j = json.loads('''
        {
            "type": "Dice",
            "value": 1
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Dice)
        self.assertDictEqual(j, obj.to_json())

    def test_market_face(self):
        j = json.loads('''
        {
            "type": "MarketFace",
            "id": 123,
            "name": "商城表情"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.MarketFace)
        self.assertDictEqual(j, obj.to_json())

    def test_music_share(self):
        j = json.loads('''
        {
            "type": "MusicShare",
            "kind": "String",
            "title": "String",
            "summary": "String",
            "jumpUrl": "String",
            "pictureUrl": "String",
            "musicUrl": "String",
            "brief": "String"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.MusicShare)
        self.assertDictEqual(j, obj.to_json())

    def test_forward(self):
        j = json.loads('''
        {
            "type": "Forward",
            "nodeList": [
                {
                    "senderId": 123,
                    "time": 0,
                    "senderName": "sender name",
                    "messageChain": [],
                    "messageId": 123
                }
            ]
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.Forward)
        self.assertDictEqual(j, obj.to_json())

    def test_file(self):
        j = json.loads('''
        {
            "type": "File",
            "id": "",
            "name": "",
            "size": 0
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.File)
        self.assertDictEqual(j, obj.to_json())

    def test_mirai_code(self):
        j = json.loads('''
        {
            "type": "MiraiCode",
            "code": "hello[mirai:at:1234567]"
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.MiraiCode)
        self.assertDictEqual(j, obj.to_json())

    def test_unsupported_message_element(self):
        j = json.loads('''
        {
            "type": "Unknown",
            "data": 12345
        }''')
        obj = MessageElement.from_json(j)
        self.assertIsInstance(obj, entities.UnsupportedMessageElement)
        self.assertDictEqual(j, obj.to_json())


if __name__ == '__main__':
    unittest.main()
