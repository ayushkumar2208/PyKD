from __future__ import annotations

from .node import BTreeNode, NodeType


class LeafNode(BTreeNode):
    def __init__(
        self,
        node_id: int,
        order: int,
    ):
        super().__init__(
            node_id,
            NodeType.LEAF,
        )

        self.order = order
        self.keys: list[str] = []
        self.values: list[int] = []
        self.next_leaf: int | None = None

    def search(self, key: str) -> int | None:
        try:
            index = self.keys.index(key)
        except ValueError:
            return None

        return self.values[index]

    def insert(
        self,
        key: str,
        value: int,
    ) -> None:
        if key in self.keys:
            index = self.keys.index(key)
            self.values[index] = value
            return

        index = 0

        while (
            index < len(self.keys)
            and self.keys[index] < key
        ):
            index += 1

        self.keys.insert(index, key)
        self.values.insert(index, value)

    def delete(self, key: str) -> bool:
        try:
            index = self.keys.index(key)
        except ValueError:
            return False

        self.keys.pop(index)
        self.values.pop(index)

        return True

    def is_full(self) -> bool:
        return len(self.keys) > self.order

    def split(self, new_node_id: int):
        middle = len(self.keys) // 2

        sibling = LeafNode(
            new_node_id,
            self.order,
        )

        sibling.keys = self.keys[middle:]
        sibling.values = self.values[middle:]

        self.keys = self.keys[:middle]
        self.values = self.values[:middle]

        sibling.next_leaf = self.next_leaf
        self.next_leaf = sibling.node_id

        return sibling

    def __len__(self) -> int:
        return len(self.keys)