from pathlib import Path

import pytest

from pykd.database import Database


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "test.pykd"


@pytest.fixture
def database(database_path: Path):
    db = Database(database_path)
    db.open()

    yield db

    db.close()


def test_database_opens(database_path: Path):
    db = Database(database_path)

    db.open()

    assert database_path.exists()

    db.close()


def test_set_and_get(database):
    database.set("name", "AK")

    assert database.get("name") == "AK"


def test_update(database):
    database.set("name", "AK")
    database.set("name", "Ayush")

    assert database.get("name") == "Ayush"


def test_missing_key(database):
    assert database.get("missing") is None


def test_exists(database):
    database.set("name", "AK")

    assert database.exists("name")
    assert not database.exists("missing")


def test_delete(database):
    database.set("name", "AK")

    assert database.delete("name")
    assert database.get("name") is None


def test_delete_missing_key(database):
    assert not database.delete("missing")


def test_keys(database):
    database.set("name", "AK")
    database.set("age", "21")

    assert set(database.keys()) == {"name", "age"}


def test_clear(database):
    database.set("name", "AK")
    database.set("age", "21")

    database.clear()

    assert database.keys() == []


def test_database_persistence(database_path: Path):
    db = Database(database_path)
    db.open()

    db.set("name", "AK")
    db.set("age", "21")

    db.close()

    db = Database(database_path)
    db.open()

    assert db.get("name") == "AK"
    assert db.get("age") == "21"

    db.close()


def test_operations_require_open_database(database_path: Path):
    db = Database(database_path)

    with pytest.raises(RuntimeError):
        db.get("name")

    with pytest.raises(RuntimeError):
        db.set("name", "AK")


def test_empty_key_is_rejected(database):
    with pytest.raises(ValueError):
        database.set("", "value")


def test_non_string_key_is_rejected(database):
    with pytest.raises(TypeError):
        database.set(123, "value")