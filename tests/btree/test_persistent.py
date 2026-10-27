from pathlib import Path

import pytest

from pykd.btree.persistent import PersistentBPlusTree


@pytest.fixture
def tree_path(tmp_path: Path):
    return tmp_path / "btree.pykd"


def open_tree(path):
    tree = PersistentBPlusTree(path, order=4)
    tree.open()
    return tree


def test_empty_persistent_tree(tree_path):
    tree = open_tree(tree_path)

    assert len(tree) == 0
    assert tree.search("missing") is None

    tree.close()


def test_insert_and_search(tree_path):
    tree = open_tree(tree_path)

    tree.insert("a", 100)

    assert tree.search("a") == 100

    tree.close()


def test_persistence_after_reopen(tree_path):
    tree = open_tree(tree_path)

    tree.insert("a", 100)
    tree.insert("b", 200)

    tree.close()

    reopened = open_tree(tree_path)

    assert reopened.search("a") == 100
    assert reopened.search("b") == 200

    reopened.close()


def test_multiple_values_persist(tree_path):
    tree = open_tree(tree_path)

    for i in range(20):
        tree.insert(
            f"key{i:03d}",
            i,
        )

    tree.close()

    reopened = open_tree(tree_path)

    for i in range(20):
        assert reopened.search(
            f"key{i:03d}"
        ) == i

    assert len(reopened) == 20

    reopened.close()


def test_items_persist(tree_path):
    tree = open_tree(tree_path)

    tree.insert("c", 3)
    tree.insert("a", 1)
    tree.insert("b", 2)

    tree.close()

    reopened = open_tree(tree_path)

    assert reopened.items() == [
        ("a", 1),
        ("b", 2),
        ("c", 3),
    ]

    reopened.close()


def test_keys_persist(tree_path):
    tree = open_tree(tree_path)

    tree.insert("c", 3)
    tree.insert("a", 1)
    tree.insert("b", 2)

    tree.close()

    reopened = open_tree(tree_path)

    assert reopened.keys() == [
        "a",
        "b",
        "c",
    ]

    reopened.close()


def test_values_persist(tree_path):
    tree = open_tree(tree_path)

    tree.insert("c", 3)
    tree.insert("a", 1)
    tree.insert("b", 2)

    tree.close()

    reopened = open_tree(tree_path)

    assert reopened.values() == [
        1,
        2,
        3,
    ]

    reopened.close()


def test_delete_persists(tree_path):
    tree = open_tree(tree_path)

    tree.insert("a", 1)
    tree.insert("b", 2)
    tree.insert("c", 3)

    assert tree.delete("b")

    tree.close()

    reopened = open_tree(tree_path)

    assert reopened.search("a") == 1
    assert reopened.search("b") is None
    assert reopened.search("c") == 3
    assert len(reopened) == 2

    reopened.close()


def test_delete_missing_key(tree_path):
    tree = open_tree(tree_path)

    assert not tree.delete("missing")

    tree.close()


def test_update_persists(tree_path):
    tree = open_tree(tree_path)

    tree.insert("a", 100)
    tree.insert("a", 200)

    tree.close()

    reopened = open_tree(tree_path)

    assert reopened.search("a") == 200
    assert len(reopened) == 1

    reopened.close()


def test_contains_persists(tree_path):
    tree = open_tree(tree_path)

    tree.insert("a", 1)

    tree.close()

    reopened = open_tree(tree_path)

    assert reopened.contains("a")
    assert not reopened.contains("b")

    reopened.close()


def test_close_without_open(tree_path):
    tree = PersistentBPlusTree(tree_path)

    tree.close()


def test_operations_require_open(tree_path):
    tree = PersistentBPlusTree(tree_path)

    with pytest.raises(RuntimeError):
        tree.search("a")

    with pytest.raises(RuntimeError):
        tree.insert("a", 1)

    with pytest.raises(RuntimeError):
        tree.delete("a")


def test_repeated_open_close(tree_path):
    tree = open_tree(tree_path)

    tree.insert("a", 1)
    tree.close()

    tree.open()

    assert tree.search("a") == 1

    tree.close()


def test_many_insertions_survive_reopen(tree_path):
    tree = open_tree(tree_path)

    for i in range(50):
        tree.insert(
            f"user{i:03d}",
            i * 10,
        )

    tree.close()

    reopened = open_tree(tree_path)

    for i in range(50):
        assert reopened.search(
            f"user{i:03d}"
        ) == i * 10

    assert len(reopened) == 50

    reopened.close()