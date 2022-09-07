import unittest
from typing import Iterable

from lightq.framework._bot import topological_sort, bot_topo_sort


class Component:
    def __init__(
        self,
        data: str,
        before: Iterable['Component'] = (),
        after: Iterable['Component'] = ()
    ):
        self.data = data
        self.before = list(before)
        self.after = list(after)

    def __eq__(self, other) -> bool:
        return isinstance(other, Component) and self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)

    def __repr__(self) -> str:
        return f'Component({self.data})'


class TopologicalSortTest(unittest.TestCase):
    def test_topo_sort_circle1(self):
        items = ['a', 'b', 'c']
        orders = [('a', 'b'), ('b', 'c'), ('c', 'a')]
        self.assertIsNone(topological_sort(items, orders))

    def test_topo_sort_circle2(self):
        items = ['a', 'b', 'c', 'd']
        orders = [('a', 'b'), ('b', 'c'), ('a', 'd'), ('c', 'a')]
        self.assertIsNone(topological_sort(items, orders))

    def test_topo_sort_single(self):
        items = ['a']
        orders = []
        self.assertEqual(['a'], topological_sort(items, orders))

    def test_topo_sort_line(self):
        items = ['a', 'b', 'c']
        orders = [('a', 'b'), ('b', 'c')]
        self.assertEqual(['a', 'b', 'c'], topological_sort(items, orders))

    def test_topo_sort(self):
        items = ['a', 'b', 'c']
        orders = [('a', 'b'), ('a', 'c')]
        self.assertIn(topological_sort(items, orders), [['a', 'b', 'c'], ['a', 'c', 'b']])

    def test_bot_topo_sort1(self):
        a = Component('a')
        b = Component('b')
        c = Component('c')
        a.before = [b, c]
        b.before = [c]
        extra_orders = [(a, b), (b, c)]
        self.assertEqual([a, b, c], bot_topo_sort([a, b, c], extra_orders))

    def test_bot_topo_sort2(self):
        a = Component('a')
        b = Component('b')
        c = Component('c')
        a.before = [b]
        c.after = [b]
        self.assertEqual([a, b, c], bot_topo_sort([a, b, c], []))

    def test_bot_topo_sort_no_default_special(self):
        default = Component('default')
        a = Component('a')
        b = Component('b')
        c = Component('c')
        a.before = [b]
        c.after = [b]
        self.assertEqual([a, b, c, default], bot_topo_sort([c, default, a, b], [], default))

    def test_bot_topo_sort_after_default_special1(self):
        default = Component('default')
        a = Component('a')
        b = Component('b')
        c = Component('c')
        a.before = [b]
        c.after = [b]
        b.after = [default]
        self.assertEqual([a, default, b, c], bot_topo_sort([default, c, a, b], [], default))

    def test_bot_topo_sort_after_default_special2(self):
        default = Component('default')
        a = Component('a')
        b = Component('b')
        c = Component('c')
        d = Component('d')
        a.before = [b]
        c.after = [b]
        b.after = [default]
        d.before = [c]
        self.assertIn(bot_topo_sort([default, c, a, b, d], [], default), [
            [a, d, default, b, c],
            [d, a, default, b, c]
        ])

    def test_bot_topo_sort_circle(self):
        default = Component('default')
        a = Component('a')
        b = Component('b')
        c = Component('c')
        a.before = [default]
        b.after = [default]
        a.after = [b]
        with self.assertRaises(Exception):
            bot_topo_sort([default, a, b, c], [], default)


if __name__ == '__main__':
    unittest.main()
