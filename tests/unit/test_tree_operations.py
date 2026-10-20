"""Tests for in-memory tree operations."""

from dataclasses import dataclass, field

from fmf.tree_operations import Merger


@dataclass
class Node:
    name: str
    data: dict = field(default_factory=dict)
    children: dict = field(default_factory=dict)
    parent: object = None
    root: object = None


def test_merge_tree_layers_merges_repeated_logical_nodes():
    first = Node('/', children={
        'a': Node('/a', children={'b': Node('/a/b', {'item+': ['a']})})})
    second = Node('/', children={
        'a': Node('/a', children={'b': Node('/a/b', {'item+': ['b']})})})

    result = Merger().merge_tree_layers([first, second])

    assert result.children['a'].children['b'].data == {'item': ['a', 'b']}
