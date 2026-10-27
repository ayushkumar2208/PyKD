import pytest

from pykd.index import Index
from pykd.record_manager import RecordLocation


@pytest.fixture
def index():
    return Index()


@pytest.fixture
def location():
    return RecordLocation(
        page_id=1,
        offset=100,
    )


def test_new_index_is_empty(index):
    assert index.is_empty()
    assert index.count() == 0
    assert len(index) == 0


def test_set_and_get(index, location):
    index.set("name", location)

    assert index.get("name") == location


def test_set_creates_entry(index, location):
    index.set("name", location)

    assert index.exists("name")
    assert "name" in index
    assert index.count() == 1


def test_update_existing_key(index):
    first = RecordLocation(
        page_id=0,
        offset=8,
    )

    second = RecordLocation(
        page_id=1,
        offset=100,
    )

    index.set("name", first)
    index.set("name", second)

    assert index.get("name") == second
    assert index.count() == 1


def test_get_missing_key(index):
    assert index.get("missing") is None


def test_delete_existing_key(index, location):
    index.set("name", location)

    assert index.delete("name")
    assert not index.exists("name")
    assert index.get("name") is None


def test_delete_missing_key(index):
    assert not index.delete("missing")


def test_keys(index):
    index.set(
        "name",
        RecordLocation(0, 8),
    )

    index.set(
        "age",
        RecordLocation(0, 30),
    )

    assert set(index.keys()) == {
        "name",
        "age",
    }


def test_values(index):
    location1 = RecordLocation(0, 8)
    location2 = RecordLocation(0, 30)

    index.set("name", location1)
    index.set("age", location2)

    assert set(index.values()) == {
        location1,
        location2,
    }


def test_items(index):
    location = RecordLocation(0, 8)

    index.set("name", location)

    assert index.items() == [
        ("name", location)
    ]


def test_clear(index):
    index.set(
        "name",
        RecordLocation(0, 8),
    )

    index.set(
        "age",
        RecordLocation(0, 30),
    )

    index.clear()

    assert index.is_empty()
    assert index.count() == 0


def test_count(index):
    index.set(
        "name",
        RecordLocation(0, 8),
    )

    index.set(
        "age",
        RecordLocation(0, 30),
    )

    index.set(
        "city",
        RecordLocation(1, 8),
    )

    assert index.count() == 3


def test_iteration(index):
    index.set(
        "name",
        RecordLocation(0, 8),
    )

    index.set(
        "age",
        RecordLocation(0, 30),
    )

    assert set(iter(index)) == {
        "name",
        "age",
    }


def test_non_string_key_is_rejected(index, location):
    with pytest.raises(TypeError):
        index.set(123, location)


def test_non_string_get_key_is_rejected(index):
    with pytest.raises(TypeError):
        index.get(123)


def test_non_string_delete_key_is_rejected(index):
    with pytest.raises(TypeError):
        index.delete(123)


def test_non_string_exists_key_is_rejected(index):
    with pytest.raises(TypeError):
        index.exists(123)


def test_empty_key_is_rejected(index, location):
    with pytest.raises(ValueError):
        index.set("", location)


def test_null_character_key_is_rejected(
    index,
    location,
):
    with pytest.raises(ValueError):
        index.set("na\x00me", location)


def test_invalid_location_is_rejected(index):
    with pytest.raises(TypeError):
        index.set("name", "invalid")


def test_multiple_keys(index):
    locations = {
        "name": RecordLocation(0, 8),
        "age": RecordLocation(0, 30),
        "city": RecordLocation(1, 8),
        "email": RecordLocation(1, 50),
    }

    for key, location in locations.items():
        index.set(key, location)

    assert index.count() == 4

    for key, location in locations.items():
        assert index.get(key) == location


def test_delete_does_not_affect_other_keys(index):
    location1 = RecordLocation(0, 8)
    location2 = RecordLocation(0, 30)

    index.set("name", location1)
    index.set("age", location2)

    index.delete("name")

    assert index.get("name") is None
    assert index.get("age") == location2
    assert index.count() == 1


def test_reinsert_after_delete(index):
    first = RecordLocation(0, 8)
    second = RecordLocation(1, 8)

    index.set("name", first)
    index.delete("name")
    index.set("name", second)

    assert index.get("name") == second
    assert index.count() == 1


def test_same_location_can_be_used_for_different_keys(index):
    location = RecordLocation(0, 8)

    index.set("name", location)
    index.set("username", location)

    assert index.get("name") == location
    assert index.get("username") == location
    assert index.count() == 2