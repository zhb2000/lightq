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


if __name__ == '__main__':
    unittest.main()
