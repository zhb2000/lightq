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


if __name__ == '__main__':
    unittest.main()
