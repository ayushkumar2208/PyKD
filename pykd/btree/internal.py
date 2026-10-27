from __future__ import annotations

from .node import BTreeNode, NodeType


class InternalNode(BTreeNode):
    def __init__(
        self,
        node_id: int,
        order: int,
    ):
        super().__init__(
            node_id,
            NodeType.INTERNAL,
        )

        self.order = order
        self.keys: list[str] = []
        self.children: list[int] = []

    def child_index(self, key: str) -> int:
        index = 0

        while (
            index < len(self.keys)
            and key >= self.keys[index]
        ):
            index += 1

        return index

    def child_for(self, key: str) -> int:
        if not self.children:
            raise ValueError(
                "Internal node has no children"
            )

        index = self.child_index(key)

        return self.children[index]

    def insert_child(
        self,
        key: str,
        child_id: int,
    ) -> None:
        index = self.child_index(key)

        self.keys.insert(index, key)
        self.children.insert(
            index + 1,
            child_id,
        )

    def is_full(self) -> bool:
        return len(self.keys) > self.order

    def __len__(self) -> int:
        return len(self.keys)