import unittest
import types
import typing

import lightq.entities
from lightq import _commons as commons


class CommonsTest(unittest.TestCase):
    def test_is_class_annotation_entity(self):
        self.assertTrue(commons.is_class_annotation(lightq.entities.Entity))

    def test_is_class_annotation_none(self):
        self.assertFalse(commons.is_class_annotation(None))
        self.assertTrue(commons.is_class_annotation(types.NoneType))

    def test_is_class_annotation_union(self):
        self.assertFalse(commons.is_class_annotation(str | int | None))
        self.assertFalse(commons.is_class_annotation(typing.Union[str, int, None]))

    def test_is_class_annotation_list(self):
        self.assertFalse(commons.is_class_annotation(list[int]))
        self.assertFalse(commons.is_class_annotation(typing.List[int]))
        self.assertTrue(commons.is_class_annotation(list))
        self.assertFalse(commons.is_class_annotation(typing.List))

    def test_to_camel_case(self):
        self.assertEqual('word', commons.to_camel_case('word'))
        self.assertEqual('from', commons.to_camel_case('from_'))
        self.assertEqual('myWord', commons.to_camel_case('my_word'))
        self.assertEqual('myWordBook', commons.to_camel_case('my_word_book'))

    def test_to_snake_case(self):
        self.assertEqual('word', commons.to_snake_case('word'))
        self.assertEqual('from_', commons.to_snake_case('from'))
        self.assertEqual('my_word', commons.to_snake_case('myWord'))
        self.assertEqual('my_word_book', commons.to_snake_case('myWordBook'))
    
    def test_class_attributes(self):
        class Base:
            common_member = 'base'
            base_member = 1

            def base_method(self):
                pass

        class Derived(Base):
            common_member = 'derived'
            derived_member = 2

            def __init__(self):
                self.instance_member = 'a'

            def __str__(self) -> str:
                return super().__str__()

            def derived_method(self):
                pass

        class_attrs = commons.get_class_attributes(Derived)
        self.assertIn('derived_member', class_attrs)
        self.assertEqual(2, class_attrs['derived_member'])
        self.assertIn('base_member', class_attrs)
        self.assertEqual(1, class_attrs['base_member'])
        self.assertIn('common_member', class_attrs)
        self.assertEqual('derived', class_attrs['common_member'])
        self.assertIn('derived_method', class_attrs)
        self.assertIn('base_method', class_attrs)
        self.assertIn('__str__', class_attrs)
        self.assertNotIn('instance_member', class_attrs)
        subset = {
            'common_member': 'derived',
            'base_member': 1,
            'derived_member': 2
        }
        self.assertEqual(class_attrs, subset | class_attrs)  # assert dict contains subset

    def test_id_token(self):
        token = commons.IdToken('token')
        self.assertNotEqual(token, '')
        self.assertNotEqual('', token)
        self.assertEqual(token, token)

    def test_id_token_in_dict(self):
        class Cls:
            def __init__(self):
                self.a = 'a'

        obj = Cls()
        token_b = commons.IdToken('b')
        obj.__dict__[token_b] = 'b'
        token_c = commons.IdToken('c')
        obj.__dict__[token_c] = 'c'
        obj.__dict__[''] = ''
        self.assertDictEqual({
            'a': 'a',
            token_b: 'b',
            token_c: 'c',
            '': ''
        }, obj.__dict__)
        self.assertEqual('a', obj.a)  # normal getattr is ok
        obj.a = 'aa'  # normal setattr is ok
        self.assertEqual('aa', obj.a)

    def test_remove_first_if_sequence(self):
        self.assertIsNone(commons.remove_first_if([], lambda x: x == 0))
        self.assertIsNone(commons.remove_first_if([1], lambda x: x == 0))
        self.assertIsNone(commons.remove_first_if([1, 2], lambda x: x == 0))
        lst = [1]
        self.assertEqual(1, commons.remove_first_if(lst, lambda x: x == 1))
        self.assertListEqual([], lst)
        lst = [-1, -1, 1]
        self.assertEqual(-1, commons.remove_first_if(lst, lambda x: abs(x) == 1))
        self.assertListEqual([-1, 1], lst)
        lst = [0, 2, -1, 2, 1, 3, 1]
        self.assertEqual(-1, commons.remove_first_if(lst, lambda x: abs(x) == 1))
        self.assertListEqual([0, 2, 2, 1, 3, 1], lst)

    def test_remove_first_if_set(self):
        self.assertIsNone(commons.remove_first_if(set(), lambda x: x == 0))
        self.assertIsNone(commons.remove_first_if({1}, lambda x: x == 0))
        self.assertIsNone(commons.remove_first_if({1, 2}, lambda x: x == 0))
        s = {1}
        self.assertEqual(1, commons.remove_first_if(s, lambda x: x == 1))
        self.assertSetEqual(set(), s)
        s = {1, 2, 3}
        self.assertEqual(1, commons.remove_first_if(s, lambda x: x == 1))
        self.assertSetEqual({2, 3}, s)


if __name__ == '__main__':
    unittest.main()
