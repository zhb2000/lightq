import unittest
import json
import copy

from lightq import entities
from lightq.entities import MessageChain, Plain


class MessageChainTest(unittest.TestCase):
    def test_message_chain(self):
        j = json.loads('''
        [
            {
                "type": "Source",
                "id": 123,
                "time": 123
            },
            {
                "type": "Plain",
                "text": "123"
            },
            {
                "type": "Plain",
                "text": "abc"
            }
        ]''')
        obj = MessageChain.from_json(j)
        self.assertIsInstance(obj, entities.MessageChain)
        self.assertEqual(obj.to_json(), j)

    def test_copy(self):
        chain1 = MessageChain([Plain('a'), Plain('b')])
        chain2 = chain1.copy()
        self.assertIsNot(chain2, chain1)
        self.assertIsInstance(chain2, MessageChain)
        self.assertEqual(chain1, chain2)
        self.assertIs(chain2[0], chain1[0])
        self.assertIs(chain2[1], chain1[1])

    def test_add(self):
        chain1 = MessageChain([Plain('a'), Plain('b')])
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b'), Plain('c')]),
            chain1 + Plain('c')
        )
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b'), Plain('c'), Plain('d')]),
            chain1 + [Plain('c'), Plain('d')]
        )

    def test_contains(self):
        chain = MessageChain([Plain('a'), Plain('b')])
        self.assertIn(Plain('a'), chain)
        self.assertNotIn(Plain('c'), chain)
        self.assertIn(Plain, chain)
        self.assertNotIn(entities.At, chain)

    def test_eq_ne(self):
        chain1 = MessageChain([Plain('a'), Plain('b')])
        chain2 = MessageChain([Plain('a'), Plain('b')])
        lst = [Plain('a'), Plain('b')]
        self.assertEqual(chain1, chain2)
        self.assertFalse(chain1 == lst)
        self.assertTrue(chain1 != lst)
        self.assertNotEqual(chain1, lst)

    def test_getitem(self):
        chain = MessageChain([Plain('a'), Plain('b'), Plain('c')])
        self.assertEqual(Plain('a'), chain[0])
        self.assertEqual(Plain('a'), chain[Plain])
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b')]),
            chain[0:2]
        )

    def test_get(self):
        chain = MessageChain([Plain('a'), Plain('b'), Plain('c')])
        # found
        self.assertEqual(Plain('a'), chain.get(0))
        self.assertEqual(Plain('a'), chain.get(Plain))
        # not found
        self.assertIsNone(chain.get(3))
        self.assertIsNone(chain.get(entities.At))
        # not found with default
        default = entities.At(0)
        self.assertEqual(default, chain.get(3, default))
        self.assertEqual(default, chain.get(entities.At, default))

    def test_iadd(self):
        chain = MessageChain([Plain('a'), Plain('b')])
        chain += Plain('c')
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b'), Plain('c')]),
            chain
        )
        chain = MessageChain([Plain('a'), Plain('b')])
        chain += [Plain('c'), Plain('d')]
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b'), Plain('c'), Plain('d')]),
            chain
        )

    def test_imul(self):
        chain = MessageChain([Plain('a'), Plain('b')])
        chain *= 2
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b'), Plain('a'), Plain('b')]),
            chain
        )

    def test_mul(self):
        chain1 = MessageChain([Plain('a'), Plain('b')])
        chain2 = chain1 * 2
        self.assertIsInstance(chain2, MessageChain)
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b'), Plain('a'), Plain('b')]),
            chain2
        )

    def test_rmul(self):
        chain1 = MessageChain([Plain('a'), Plain('b')])
        chain2 = 2 * chain1
        self.assertIsInstance(chain2, MessageChain)
        self.assertEqual(
            MessageChain([Plain('a'), Plain('b'), Plain('a'), Plain('b')]),
            chain2
        )

    def test_repr(self):
        chain = MessageChain([Plain('a'), Plain('b')])
        self.assertEqual("MessageChain[Plain(text='a'), Plain(text='b')]", repr(chain))

    def test_str(self):
        chain = MessageChain([entities.Source(0, 0), Plain('a'), Plain('b'), entities.AtAll()])
        self.assertEqual('ab@全体成员', str(chain))

    def test_get_all(self):
        chain = MessageChain([entities.Source(0, 0), Plain('a'), Plain('b'), entities.AtAll()])
        self.assertListEqual([Plain('a'), Plain('b')], chain.get_all(Plain))

    def test_copy_copy(self):
        chain1 = MessageChain([Plain('a'), Plain('b')])
        chain2 = copy.copy(chain1)
        self.assertIsNot(chain2, chain1)
        self.assertIsInstance(chain2, MessageChain)
        self.assertEqual(chain1, chain2)
        self.assertIs(chain2[0], chain1[0])
        self.assertIs(chain2[1], chain1[1])

    def test_deepcopy(self):
        chain1 = MessageChain([Plain('a'), Plain('b')])
        chain2 = copy.deepcopy(chain1)
        self.assertIsNot(chain2, chain1)
        self.assertIsInstance(chain2, MessageChain)
        self.assertEqual(chain1, chain2)
        self.assertIsNot(chain2[0], chain1[0])
        self.assertIsNot(chain2[1], chain1[1])


if __name__ == '__main__':
    unittest.main()
