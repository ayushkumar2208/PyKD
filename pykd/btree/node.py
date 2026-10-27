from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeType(Enum):
    LEAF = "leaf"
    INTERNAL = "internal"


@dataclass
class BTreeNode:
    node_id: int
    node_type: NodeType

    @property
    def is_leaf(self) -> bool:
        return self.node_type == NodeType.LEAF

    @property
    def is_internal(self) -> bool:
        return self.node_type == NodeType.INTERNAL