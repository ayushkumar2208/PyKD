from pathlib import Path

import pytest

from pykd.page import PAGE_SIZE
from pykd.page_manager import PageManager
from pykd.record import Record, RecordType
from pykd.record_manager import (
    RECORD_LENGTH_SIZE,
    RecordLocation,
    RecordManager,
    RecordManagerError,
)


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "records.pykd"


@pytest.fixture
def manager(database_path: Path):
    page_manager = PageManager(database_path)
    page_manager.open()

    record_manager = RecordManager(page_manager)

    yield record_manager

    page_manager.close()


def test_append_record(manager: RecordManager):
    record = Record("name", "AK")

    location = manager.append(record)

    assert isinstance(location, RecordLocation)
    assert location.page_id == 0


def test_append_and_read_record(manager: RecordManager):
    record = Record("name", "AK")

    location = manager.append(record)

    assert manager.read(location) == record


def test_record_location_contains_correct_offset(
    manager: RecordManager,
):
    location = manager.append(
        Record("name", "AK")
    )

    assert location.page_id == 0
    assert location.offset > 0


def test_multiple_records(manager: RecordManager):
    records = [
        Record("name", "AK"),
        Record("age", "22"),
        Record("city", "Delhi"),
    ]

    locations = [
        manager.append(record)
        for record in records
    ]

    restored = [
        manager.read(location)
        for location in locations
    ]

    assert restored == records


def test_multiple_records_have_different_locations(
    manager: RecordManager,
):
    location1 = manager.append(
        Record("a", "1")
    )
    location2 = manager.append(
        Record("b", "2")
    )

    assert location1 != location2


def test_scan_page(manager: RecordManager):
    records = [
        Record("name", "AK"),
        Record("age", "22"),
        Record("city", "Delhi"),
    ]

    for record in records:
        manager.append(record)

    scanned = [
        record
        for _, record in manager.scan_page(0)
    ]

    assert scanned == records


def test_scan_all_records(manager: RecordManager):
    records = [
        Record("name", "AK"),
        Record("age", "22"),
        Record("city", "Delhi"),
    ]

    for record in records:
        manager.append(record)

    scanned = [
        record
        for _, record in manager.scan()
    ]

    assert scanned == records


def test_find_record(manager: RecordManager):
    manager.append(
        Record("name", "AK")
    )
    manager.append(
        Record("age", "22")
    )

    location = manager.find("age")

    assert location is not None
    assert manager.read(location) == Record(
        "age",
        "22",
    )


def test_find_missing_record(manager: RecordManager):
    manager.append(
        Record("name", "AK")
    )

    assert manager.find("missing") is None


def test_find_returns_latest_record(
    manager: RecordManager,
):
    manager.append(
        Record("name", "AK")
    )

    manager.append(
        Record("name", "Ayush")
    )

    location = manager.find("name")

    assert location is not None
    assert manager.read(location) == Record(
        "name",
        "Ayush",
    )


def test_find_returns_none_after_delete(
    manager: RecordManager,
):
    manager.append(
        Record("name", "AK")
    )

    manager.append(
        Record.delete("name")
    )

    assert manager.find("name") is None


def test_delete_record_is_stored(
    manager: RecordManager,
):
    location = manager.append(
        Record.delete("name")
    )

    restored = manager.read(location)

    assert restored.record_type == RecordType.DELETE
    assert restored.key == "name"
    assert restored.value == ""


def test_delete_record_is_scanned(
    manager: RecordManager,
):
    manager.append(
        Record("name", "AK")
    )

    manager.append(
        Record.delete("name")
    )

    scanned = [
        record
        for _, record in manager.scan()
    ]

    assert scanned == [
        Record("name", "AK"),
        Record.delete("name"),
    ]


def test_find_all(manager: RecordManager):
    manager.append(
        Record("name", "AK")
    )

    manager.append(
        Record("age", "22")
    )

    manager.append(
        Record("name", "Ayush")
    )

    locations = manager.find_all("name")

    assert len(locations) == 2

    values = [
        manager.read(location).value
        for location in locations
    ]

    assert values == [
        "AK",
        "Ayush",
    ]


def test_find_all_includes_delete_record(
    manager: RecordManager,
):
    manager.append(
        Record("name", "AK")
    )

    manager.append(
        Record.delete("name")
    )

    locations = manager.find_all("name")

    assert len(locations) == 2

    assert manager.read(
        locations[0]
    ) == Record("name", "AK")

    assert manager.read(
        locations[1]
    ) == Record.delete("name")


def test_count(manager: RecordManager):
    manager.append(
        Record("a", "1")
    )

    manager.append(
        Record("b", "2")
    )

    manager.append(
        Record("c", "3")
    )

    assert manager.count() == 3


def test_count_includes_delete_records(
    manager: RecordManager,
):
    manager.append(
        Record("name", "AK")
    )

    manager.append(
        Record.delete("name")
    )

    assert manager.count() == 2


def test_page_record_count(
    manager: RecordManager,
):
    manager.append(
        Record("a", "1")
    )

    manager.append(
        Record("b", "2")
    )

    assert manager.page_record_count(0) == 2


def test_records_persist_after_reopen(
    database_path: Path,
):
    page_manager = PageManager(database_path)
    page_manager.open()

    record_manager = RecordManager(page_manager)

    location = record_manager.append(
        Record("name", "AK")
    )

    page_manager.close()

    page_manager = PageManager(database_path)
    page_manager.open()

    record_manager = RecordManager(page_manager)

    assert record_manager.read(location) == Record(
        "name",
        "AK",
    )

    page_manager.close()


def test_delete_record_persists_after_reopen(
    database_path: Path,
):
    page_manager = PageManager(database_path)
    page_manager.open()

    record_manager = RecordManager(page_manager)

    location = record_manager.append(
        Record.delete("name")
    )

    page_manager.close()

    page_manager = PageManager(database_path)
    page_manager.open()

    record_manager = RecordManager(page_manager)

    restored = record_manager.read(location)

    assert restored == Record.delete("name")

    page_manager.close()


def test_large_records_allocate_multiple_pages(
    manager: RecordManager,
):
    value = "x" * 2000

    manager.append(
        Record("key1", value)
    )

    manager.append(
        Record("key2", value)
    )

    manager.append(
        Record("key3", value)
    )

    assert manager.page_manager.page_count() >= 2
    assert manager.count() == 3


def test_records_on_different_pages_are_read_correctly(
    manager: RecordManager,
):
    value = "x" * 2000

    first = Record("first", value)
    second = Record("second", value)
    third = Record("third", value)

    location1 = manager.append(first)
    location2 = manager.append(second)
    location3 = manager.append(third)

    assert manager.read(location1) == first
    assert manager.read(location2) == second
    assert manager.read(location3) == third


def test_empty_page_has_zero_records(
    manager: RecordManager,
):
    manager.page_manager.allocate_page()

    assert manager.page_record_count(0) == 0
    assert manager.count() == 0


def test_read_invalid_location(
    manager: RecordManager,
):
    manager.page_manager.allocate_page()

    location = RecordLocation(
        page_id=0,
        offset=8,
    )

    with pytest.raises(RecordManagerError):
        manager.read(location)


def test_invalid_record_type(
    manager: RecordManager,
):
    with pytest.raises(TypeError):
        manager.append("invalid")


def test_invalid_location_type(
    manager: RecordManager,
):
    with pytest.raises(TypeError):
        manager.read("invalid")


def test_find_requires_string_key(
    manager: RecordManager,
):
    with pytest.raises(TypeError):
        manager.find(123)


def test_find_all_requires_string_key(
    manager: RecordManager,
):
    with pytest.raises(TypeError):
        manager.find_all(123)


def test_record_size_prefix_is_present(
    manager: RecordManager,
):
    record = Record("name", "AK")

    location = manager.append(record)

    page = manager.page_manager.read_page(
        location.page_id
    )

    raw_length = page.read(
        location.offset,
        RECORD_LENGTH_SIZE,
    )

    record_length = int.from_bytes(
        raw_length,
        byteorder="big",
    )

    assert record_length == len(
        record.serialize()
    )


def test_delete_record_size_prefix_is_present(
    manager: RecordManager,
):
    record = Record.delete("name")

    location = manager.append(record)

    page = manager.page_manager.read_page(
        location.page_id
    )

    raw_length = page.read(
        location.offset,
        RECORD_LENGTH_SIZE,
    )

    record_length = int.from_bytes(
        raw_length,
        byteorder="big",
    )

    assert record_length == len(
        record.serialize()
    )


def test_page_allocation_for_large_records(
    manager: RecordManager,
):
    value = "x" * (PAGE_SIZE // 2)

    locations = [
        manager.append(
            Record(f"key{i}", value)
        )
        for i in range(4)
    ]

    page_ids = {
        location.page_id
        for location in locations
    }

    assert len(page_ids) >= 2