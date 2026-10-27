from __future__ import annotations

from .internal import InternalNode
from .leaf import LeafNode
from .node import BTreeNode


class BPlusTree:
    def __init__(self, order: int = 4):
        if order < 3:
            raise ValueError(
                "B+ tree order must be at least 3"
            )

        self.order = order
        self._next_id = 0
        self._nodes: dict[int, BTreeNode] = {}

        self.root = self._new_leaf()

    def search(self, key: str) -> int | None:
        leaf = self._find_leaf(key)

        return leaf.search(key)

    def insert(
        self,
        key: str,
        value: int,
    ) -> None:
        leaf = self._find_leaf(key)

        leaf.insert(key, value)

        if not leaf.is_full():
            return

        sibling = leaf.split(
            self._allocate_id()
        )

        self._nodes[sibling.node_id] = sibling

        separator = sibling.keys[0]

        self._insert_into_parent(
            leaf.node_id,
            separator,
            sibling.node_id,
        )

    def delete(self, key: str) -> bool:
        leaf = self._find_leaf(key)

        return leaf.delete(key)

    def contains(self, key: str) -> bool:
        return self.search(key) is not None

    def items(self) -> list[tuple[str, int]]:
        leaves = []

        node = self._leftmost_leaf()

        while node is not None:
            for key, value in zip(
                node.keys,
                node.values,
            ):
                leaves.append((key, value))

            if node.next_leaf is None:
                break

            node = self._nodes[node.next_leaf]

        return leaves

    def keys(self) -> list[str]:
        return [
            key
            for key, _ in self.items()
        ]

    def values(self) -> list[int]:
        return [
            value
            for _, value in self.items()
        ]

    def __len__(self) -> int:
        return sum(
            len(node.keys)
            for node in self._nodes.values()
            if isinstance(node, LeafNode)
        )

    def _find_leaf(self, key: str) -> LeafNode:
        node = self._nodes[self.root.node_id]

        while isinstance(node, InternalNode):
            child_id = node.child_for(key)
            node = self._nodes[child_id]

        return node

    def _leftmost_leaf(self) -> LeafNode:
        node = self._nodes[self.root.node_id]

        while isinstance(node, InternalNode):
            node = self._nodes[node.children[0]]

        return node

    def _insert_into_parent(
        self,
        left_id: int,
        key: str,
        right_id: int,
    ) -> None:
        if self.root.node_id == left_id:
            new_root = InternalNode(
                self._allocate_id(),
                self.order,
            )

            new_root.keys = [key]
            new_root.children = [
                left_id,
                right_id,
            ]

            self._nodes[new_root.node_id] = new_root
            self.root = new_root

            return

        parent = self._find_parent(
            self.root.node_id,
            left_id,
        )

        parent.insert_child(
            key,
            right_id,
        )

        if parent.is_full():
            self._split_internal(parent)

    def _split_internal(
        self,
        node: InternalNode,
    ) -> None:
        middle = len(node.keys) // 2
        separator = node.keys[middle]

        sibling = InternalNode(
            self._allocate_id(),
            self.order,
        )

        sibling.keys = node.keys[
            middle + 1:
        ]

        sibling.children = node.children[
            middle + 1:
        ]

        node.keys = node.keys[:middle]
        node.children = node.children[:middle + 1]

        self._nodes[sibling.node_id] = sibling

        self._insert_into_parent(
            node.node_id,
            separator,
            sibling.node_id,
        )

    def _find_parent(
        self,
        current_id: int,
        child_id: int,
    ) -> InternalNode:
        current = self._nodes[current_id]

        if not isinstance(
            current,
            InternalNode,
        ):
            raise ValueError(
                "Parent not found"
            )

        if child_id in current.children:
            return current

        for descendant_id in current.children:
            descendant = self._nodes[
                descendant_id
            ]

            if isinstance(
                descendant,
                InternalNode,
            ):
                try:
                    return self._find_parent(
                        descendant_id,
                        child_id,
                    )
                except ValueError:
                    pass

        raise ValueError(
            "Parent not found"
        )

    def _new_leaf(self) -> LeafNode:
        node = LeafNode(
            self._allocate_id(),
            self.order,
        )

        self._nodes[node.node_id] = node

        return node

    def _allocate_id(self) -> int:
        node_id = self._next_id
        self._next_id += 1
        return node_id