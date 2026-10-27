import pytest

from pykd.btree import BPlusTree


def test_empty_tree():
    tree = BPlusTree()

    assert len(tree) == 0
    assert tree.search("missing") is None


def test_insert_and_search():
    tree = BPlusTree()

    tree.insert("a", 10)

    assert tree.search("a") == 10


def test_missing_key():
    tree = BPlusTree()

    tree.insert("a", 10)

    assert tree.search("b") is None


def test_update_existing_key():
    tree = BPlusTree()

    tree.insert("a", 10)
    tree.insert("a", 20)

    assert tree.search("a") == 20
    assert len(tree) == 1


def test_multiple_keys():
    tree = BPlusTree()

    tree.insert("a", 1)
    tree.insert("b", 2)
    tree.insert("c", 3)

    assert tree.search("a") == 1
    assert tree.search("b") == 2
    assert tree.search("c") == 3


def test_sorted_items():
    tree = BPlusTree()

    tree.insert("d", 4)
    tree.insert("a", 1)
    tree.insert("c", 3)
    tree.insert("b", 2)

    assert tree.items() == [
        ("a", 1),
        ("b", 2),
        ("c", 3),
        ("d", 4),
    ]


def test_keys_are_sorted():
    tree = BPlusTree()

    for key in ["d", "b", "a", "c"]:
        tree.insert(key, 1)

    assert tree.keys() == [
        "a",
        "b",
        "c",
        "d",
    ]


def test_values_follow_keys():
    tree = BPlusTree()

    tree.insert("c", 30)
    tree.insert("a", 10)
    tree.insert("b", 20)

    assert tree.values() == [
        10,
        20,
        30,
    ]


def test_contains():
    tree = BPlusTree()

    tree.insert("a", 1)

    assert tree.contains("a")
    assert not tree.contains("b")


def test_delete():
    tree = BPlusTree()

    tree.insert("a", 1)

    assert tree.delete("a")
    assert tree.search("a") is None


def test_delete_missing():
    tree = BPlusTree()

    assert not tree.delete("missing")


def test_many_insertions():
    tree = BPlusTree(order=4)

    for i in range(100):
        tree.insert(
            f"key{i:03d}",
            i,
        )

    for i in range(100):
        assert tree.search(
            f"key{i:03d}"
        ) == i

    assert len(tree) == 100


def test_many_insertions_sorted():
    tree = BPlusTree(order=4)

    for i in reversed(range(100)):
        tree.insert(
            f"key{i:03d}",
            i,
        )

    keys = tree.keys()

    assert keys == sorted(keys)


def test_small_order_causes_splits():
    tree = BPlusTree(order=3)

    for i in range(20):
        tree.insert(
            str(i),
            i,
        )

    for i in range(20):
        assert tree.search(str(i)) == i

    assert len(tree) == 20


def test_invalid_order():
    with pytest.raises(ValueError):
        BPlusTree(order=2)