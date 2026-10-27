from pathlib import Path

import pytest

from pykd.storage import StorageEngine, StorageError


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "database.pykd"


@pytest.fixture
def engine(database_path: Path):
    engine = StorageEngine(database_path)
    engine.open()
    yield engine
    engine.close()


def test_open_close(database_path):
    engine = StorageEngine(database_path)
    engine.open()
    engine.close()


def test_put_get(engine):
    engine.put("name", "AK")

    assert engine.get("name") == "AK"


def test_missing_key(engine):
    assert engine.get("missing") is None


def test_update(engine):
    engine.put("name", "AK")
    engine.put("name", "Ayush")

    assert engine.get("name") == "Ayush"


def test_exists(engine):
    assert not engine.exists("name")

    engine.put("name", "AK")

    assert engine.exists("name")


def test_delete(engine):
    engine.put("name", "AK")

    assert engine.delete("name")
    assert engine.get("name") is None
    assert not engine.exists("name")


def test_delete_missing(engine):
    assert not engine.delete("missing")


def test_keys(engine):
    engine.put("name", "AK")
    engine.put("age", "22")
    engine.put("city", "Delhi")

    assert set(engine.keys()) == {
        "name",
        "age",
        "city",
    }


def test_clear(engine):
    engine.put("name", "AK")
    engine.put("age", "22")

    engine.clear()

    assert engine.keys() == []
    assert engine.get("name") is None
    assert engine.get("age") is None


def test_index_count(engine):
    assert engine.index_count() == 0

    engine.put("name", "AK")
    engine.put("age", "22")

    assert engine.index_count() == 2


def test_update_keeps_one_index_entry(engine):
    engine.put("name", "AK")
    engine.put("name", "Ayush")
    engine.put("name", "A K")

    assert engine.index_count() == 1
    assert engine.get("name") == "A K"


def test_delete_removes_index_entry(engine):
    engine.put("name", "AK")

    assert engine.index_count() == 1

    engine.delete("name")

    assert engine.index_count() == 0


def test_persistence(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    engine.put("name", "AK")
    engine.put("age", "22")

    engine.close()

    engine = StorageEngine(database_path)
    engine.open()

    assert engine.get("name") == "AK"
    assert engine.get("age") == "22"

    engine.close()


def test_deleted_key_stays_deleted(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    engine.put("name", "AK")
    engine.delete("name")

    engine.close()

    engine = StorageEngine(database_path)
    engine.open()

    assert engine.get("name") is None
    assert not engine.exists("name")
    assert engine.index_count() == 0

    engine.close()


def test_update_persists(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    engine.put("name", "AK")
    engine.put("name", "Ayush")

    engine.close()

    engine = StorageEngine(database_path)
    engine.open()

    assert engine.get("name") == "Ayush"

    engine.close()


def test_delete_then_reinsert(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    engine.put("name", "AK")
    engine.delete("name")
    engine.put("name", "Ayush")

    assert engine.get("name") == "Ayush"
    assert engine.index_count() == 1

    engine.close()

    engine = StorageEngine(database_path)
    engine.open()

    assert engine.get("name") == "Ayush"

    engine.close()


def test_multiple_keys(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    engine.put("name", "AK")
    engine.put("age", "22")
    engine.put("city", "Delhi")

    engine.delete("age")

    assert engine.get("name") == "AK"
    assert engine.get("age") is None
    assert engine.get("city") == "Delhi"

    engine.close()


def test_multiple_keys_after_reopen(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    engine.put("name", "AK")
    engine.put("age", "22")
    engine.put("city", "Delhi")
    engine.delete("age")

    engine.close()

    engine = StorageEngine(database_path)
    engine.open()

    assert engine.get("name") == "AK"
    assert engine.get("age") is None
    assert engine.get("city") == "Delhi"

    engine.close()


def test_record_count(engine):
    assert engine.record_count() == 0

    engine.put("name", "AK")

    assert engine.record_count() == 1


def test_record_count_includes_updates(engine):
    engine.put("name", "AK")
    engine.put("name", "Ayush")

    assert engine.record_count() == 2


def test_record_count_includes_delete(engine):
    engine.put("name", "AK")
    engine.delete("name")

    assert engine.record_count() == 2


def test_page_count(engine):
    assert engine.page_count() == 0

    engine.put("name", "AK")

    assert engine.page_count() >= 1


def test_invalid_key(engine):
    with pytest.raises(TypeError):
        engine.put(123, "value")


def test_invalid_get_key(engine):
    with pytest.raises(TypeError):
        engine.get(123)


def test_invalid_delete_key(engine):
    with pytest.raises(TypeError):
        engine.delete(123)


def test_invalid_exists_key(engine):
    with pytest.raises(TypeError):
        engine.exists(123)


def test_empty_key(engine):
    with pytest.raises(ValueError):
        engine.put("", "value")


def test_null_key(engine):
    with pytest.raises(ValueError):
        engine.put("na\x00me", "value")


def test_invalid_value(engine):
    with pytest.raises(TypeError):
        engine.put("age", 22)


def test_operations_before_open(database_path):
    engine = StorageEngine(database_path)

    with pytest.raises(StorageError):
        engine.get("name")

    with pytest.raises(StorageError):
        engine.put("name", "AK")

    with pytest.raises(StorageError):
        engine.delete("name")

    with pytest.raises(StorageError):
        engine.keys()


def test_clear_persists(database_path):
    engine = StorageEngine(database_path)
    engine.open()

    engine.put("name", "AK")
    engine.put("age", "22")
    engine.clear()

    engine.close()

    engine = StorageEngine(database_path)
    engine.open()

    assert engine.keys() == []
    assert engine.get("name") is None
    assert engine.get("age") is None

    engine.close()


def test_reopen_empty_database(database_path):
    engine = StorageEngine(database_path)
    engine.open()
    engine.close()

    engine = StorageEngine(database_path)
    engine.open()

    assert engine.keys() == []
    assert engine.index_count() == 0

    engine.close()


def test_repeated_delete(engine):
    engine.put("name", "AK")

    assert engine.delete("name")
    assert not engine.delete("name")

    assert engine.get("name") is None