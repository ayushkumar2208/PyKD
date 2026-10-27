from __future__ import annotations

import struct
from pathlib import Path

from ..page import PAGE_HEADER_SIZE, PAGE_SIZE, Page
from ..page_manager import PageManager
from .internal import InternalNode
from .leaf import LeafNode


BTREE_META_PAGE_TYPE = 2
BTREE_NODE_PAGE_TYPE = 3

META_FORMAT = ">q"
META_SIZE = struct.calcsize(META_FORMAT)

NODE_HEADER_FORMAT = ">BBiq"
NODE_HEADER_SIZE = struct.calcsize(NODE_HEADER_FORMAT)

LEAF_ENTRY_HEADER_FORMAT = ">Hq"
LEAF_ENTRY_HEADER_SIZE = struct.calcsize(
    LEAF_ENTRY_HEADER_FORMAT
)


class PersistentBPlusTreeError(Exception):
    pass


class PersistentBPlusTree:
    def __init__(
        self,
        path: str | Path,
        order: int = 4,
    ):
        if order < 3:
            raise ValueError(
                "B+ tree order must be at least 3"
            )

        self.path = Path(path)
        self.order = order
        self.page_manager = PageManager(self.path)

        self.root_id: int | None = None
        self._opened = False

    def open(self) -> None:
        if self._opened:
            return

        self.page_manager.open()

        try:
            if self.page_manager.page_count() == 0:
                self.page_manager.allocate_page()

                root = self._allocate_leaf()

                self.root_id = root.node_id
                self._write_metadata()
            else:
                self._read_metadata()

            self._opened = True

        except Exception:
            self.page_manager.close()
            raise

    def close(self) -> None:
        if not self._opened:
            return

        try:
            self.page_manager.sync()
        finally:
            self.page_manager.close()
            self._opened = False
            self.root_id = None

    def insert(
        self,
        key: str,
        value: int,
    ) -> None:
        self._ensure_open()

        leaf = self._find_leaf(key)

        leaf.insert(key, value)

        if not leaf.is_full():
            self._write_node(leaf)
            self.page_manager.sync()
            return

        sibling = self._split_leaf(leaf)

        self._insert_into_parent(
            leaf.node_id,
            sibling.keys[0],
            sibling.node_id,
        )

        self.page_manager.sync()

    def search(
        self,
        key: str,
    ) -> int | None:
        self._ensure_open()

        leaf = self._find_leaf(key)

        return leaf.search(key)

    def delete(
        self,
        key: str,
    ) -> bool:
        self._ensure_open()

        leaf = self._find_leaf(key)

        deleted = leaf.delete(key)

        if not deleted:
            return False

        self._write_node(leaf)
        self.page_manager.sync()

        return True

    def contains(self, key: str) -> bool:
        return self.search(key) is not None

    def items(self) -> list[tuple[str, int]]:
        self._ensure_open()

        result: list[tuple[str, int]] = []

        leaf = self._leftmost_leaf()

        while True:
            result.extend(
                zip(
                    leaf.keys,
                    leaf.values,
                )
            )

            if leaf.next_leaf is None:
                break

            leaf = self._read_node(
                leaf.next_leaf
            )

            if not isinstance(
                leaf,
                LeafNode,
            ):
                raise PersistentBPlusTreeError(
                    "Leaf chain contains "
                    "a non-leaf node"
                )

        return result

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
        return len(self.items())

    def _find_leaf(
        self,
        key: str,
    ) -> LeafNode:
        if self.root_id is None:
            raise PersistentBPlusTreeError(
                "Root is not initialized"
            )

        node = self._read_node(
            self.root_id
        )

        while isinstance(
            node,
            InternalNode,
        ):
            child_id = node.child_for(key)
            node = self._read_node(child_id)

        if not isinstance(
            node,
            LeafNode,
        ):
            raise PersistentBPlusTreeError(
                "Search did not end at a leaf"
            )

        return node

    def _leftmost_leaf(self) -> LeafNode:
        if self.root_id is None:
            raise PersistentBPlusTreeError(
                "Root is not initialized"
            )

        node = self._read_node(
            self.root_id
        )

        while isinstance(
            node,
            InternalNode,
        ):
            node = self._read_node(
                node.children[0]
            )

        if not isinstance(
            node,
            LeafNode,
        ):
            raise PersistentBPlusTreeError(
                "Leftmost node is not a leaf"
            )

        return node

    def _insert_into_parent(
        self,
        left_id: int,
        separator: str,
        right_id: int,
    ) -> None:
        if self.root_id == left_id:
            root = self._allocate_internal()

            root.keys = [separator]
            root.children = [
                left_id,
                right_id,
            ]

            self._write_node(root)

            self.root_id = root.node_id

            self._write_metadata()

            return

        parent = self._find_parent(
            self.root_id,
            left_id,
        )

        parent.insert_child(
            separator,
            right_id,
        )

        self._write_node(parent)

        if parent.is_full():
            self._split_internal(parent)

    def _split_leaf(
        self,
        leaf: LeafNode,
    ) -> LeafNode:
        sibling = self._allocate_leaf()

        middle = len(leaf.keys) // 2

        sibling.keys = leaf.keys[middle:]
        sibling.values = leaf.values[middle:]

        leaf.keys = leaf.keys[:middle]
        leaf.values = leaf.values[:middle]

        sibling.next_leaf = leaf.next_leaf
        leaf.next_leaf = sibling.node_id

        self._write_node(leaf)
        self._write_node(sibling)

        return sibling

    def _split_internal(
        self,
        node: InternalNode,
    ) -> None:
        middle = len(node.keys) // 2

        separator = node.keys[middle]

        sibling = self._allocate_internal()

        sibling.keys = node.keys[
            middle + 1:
        ]

        sibling.children = node.children[
            middle + 1:
        ]

        node.keys = node.keys[:middle]

        node.children = node.children[
            :middle + 1
        ]

        self._write_node(node)
        self._write_node(sibling)

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
        current = self._read_node(
            current_id
        )

        if not isinstance(
            current,
            InternalNode,
        ):
            raise PersistentBPlusTreeError(
                "Parent not found"
            )

        if child_id in current.children:
            return current

        for descendant_id in current.children:
            descendant = self._read_node(
                descendant_id
            )

            if isinstance(
                descendant,
                InternalNode,
            ):
                try:
                    return self._find_parent(
                        descendant_id,
                        child_id,
                    )
                except PersistentBPlusTreeError:
                    continue

        raise PersistentBPlusTreeError(
            "Parent not found"
        )

    def _allocate_leaf(self) -> LeafNode:
        page = self.page_manager.allocate_page()

        node = LeafNode(
            page.page_id,
            self.order,
        )

        self._write_node(node)

        return node

    def _allocate_internal(self) -> InternalNode:
        page = self.page_manager.allocate_page()

        node = InternalNode(
            page.page_id,
            self.order,
        )

        self._write_node(node)

        return node

    def _write_node(
        self,
        node: LeafNode | InternalNode,
    ) -> None:
        page = Page(
            page_id=node.node_id,
            page_type=BTREE_NODE_PAGE_TYPE,
        )

        if isinstance(node, LeafNode):
            payload = self._serialize_leaf(node)
        else:
            payload = self._serialize_internal(node)

        if (
            PAGE_HEADER_SIZE + len(payload)
            > PAGE_SIZE
        ):
            raise PersistentBPlusTreeError(
                "B+ tree node exceeds page size"
            )

        page.write(
            PAGE_HEADER_SIZE,
            payload,
        )

        self.page_manager.write_page(page)

    def _read_node(
        self,
        node_id: int,
    ) -> LeafNode | InternalNode:
        page = self.page_manager.read_page(
            node_id
        )

        if page.page_type != BTREE_NODE_PAGE_TYPE:
            raise PersistentBPlusTreeError(
                f"Page {node_id} is not "
                "a B+ tree node"
            )

        raw = page.read(
            PAGE_HEADER_SIZE,
            PAGE_SIZE - PAGE_HEADER_SIZE,
        )

        if len(raw) < NODE_HEADER_SIZE:
            raise PersistentBPlusTreeError(
                f"Invalid B+ tree page {node_id}"
            )

        node_type, _, count, next_id = struct.unpack(
            NODE_HEADER_FORMAT,
            raw[:NODE_HEADER_SIZE],
        )

        payload = raw[NODE_HEADER_SIZE:]

        if node_type == 1:
            return self._deserialize_leaf(
                node_id,
                count,
                next_id,
                payload,
            )

        if node_type == 2:
            return self._deserialize_internal(
                node_id,
                count,
                payload,
            )

        raise PersistentBPlusTreeError(
            f"Unknown node type: {node_type}"
        )

    def _serialize_leaf(
        self,
        node: LeafNode,
    ) -> bytes:
        next_id = (
            node.next_leaf
            if node.next_leaf is not None
            else -1
        )

        payload = struct.pack(
            NODE_HEADER_FORMAT,
            1,
            0,
            len(node.keys),
            next_id,
        )

        for key, value in zip(
            node.keys,
            node.values,
        ):
            encoded = key.encode("utf-8")

            payload += struct.pack(
                LEAF_ENTRY_HEADER_FORMAT,
                len(encoded),
                value,
            )

            payload += encoded

        return payload

    def _serialize_internal(
        self,
        node: InternalNode,
    ) -> bytes:
        payload = struct.pack(
            NODE_HEADER_FORMAT,
            2,
            0,
            len(node.keys),
            -1,
        )

        for key in node.keys:
            encoded = key.encode("utf-8")

            payload += struct.pack(
                ">H",
                len(encoded),
            )

            payload += encoded

        for child_id in node.children:
            payload += struct.pack(
                ">q",
                child_id,
            )

        return payload

    def _deserialize_leaf(
        self,
        node_id: int,
        count: int,
        next_id: int,
        payload: bytes,
    ) -> LeafNode:
        node = LeafNode(
            node_id,
            self.order,
        )

        offset = 0

        for _ in range(count):
            if (
                offset + LEAF_ENTRY_HEADER_SIZE
                > len(payload)
            ):
                raise PersistentBPlusTreeError(
                    "Corrupt leaf page"
                )

            key_length, value = struct.unpack(
                LEAF_ENTRY_HEADER_FORMAT,
                payload[
                    offset:
                    offset + LEAF_ENTRY_HEADER_SIZE
                ],
            )

            offset += LEAF_ENTRY_HEADER_SIZE

            end = offset + key_length

            if end > len(payload):
                raise PersistentBPlusTreeError(
                    "Corrupt leaf key"
                )

            key = payload[
                offset:end
            ].decode("utf-8")

            offset = end

            node.keys.append(key)
            node.values.append(value)

        node.next_leaf = (
            None
            if next_id < 0
            else next_id
        )

        return node

    def _deserialize_internal(
        self,
        node_id: int,
        count: int,
        payload: bytes,
    ) -> InternalNode:
        node = InternalNode(
            node_id,
            self.order,
        )

        offset = 0

        for _ in range(count):
            if offset + 2 > len(payload):
                raise PersistentBPlusTreeError(
                    "Corrupt internal page"
                )

            key_length = struct.unpack(
                ">H",
                payload[offset:offset + 2],
            )[0]

            offset += 2

            end = offset + key_length

            if end > len(payload):
                raise PersistentBPlusTreeError(
                    "Corrupt internal key"
                )

            key = payload[
                offset:end
            ].decode("utf-8")

            offset = end

            node.keys.append(key)

        for _ in range(count + 1):
            if offset + 8 > len(payload):
                raise PersistentBPlusTreeError(
                    "Corrupt internal child list"
                )

            child_id = struct.unpack(
                ">q",
                payload[offset:offset + 8],
            )[0]

            offset += 8

            node.children.append(child_id)

        return node

    def _write_metadata(self) -> None:
        if self.root_id is None:
            raise PersistentBPlusTreeError(
                "Cannot write metadata without root"
            )

        page = Page(
            page_id=0,
            page_type=BTREE_META_PAGE_TYPE,
        )

        payload = struct.pack(
            META_FORMAT,
            self.root_id,
        )

        page.write(
            PAGE_HEADER_SIZE,
            payload,
        )

        self.page_manager.write_page(page)

    def _read_metadata(self) -> None:
        page = self.page_manager.read_page(0)

        if page.page_type != BTREE_META_PAGE_TYPE:
            raise PersistentBPlusTreeError(
                "Invalid B+ tree metadata page"
            )

        raw = page.read(
            PAGE_HEADER_SIZE,
            META_SIZE,
        )

        self.root_id = struct.unpack(
            META_FORMAT,
            raw,
        )[0]

    def _ensure_open(self) -> None:
        if not self._opened:
            raise RuntimeError(
                "Persistent B+ tree is not open"
            )