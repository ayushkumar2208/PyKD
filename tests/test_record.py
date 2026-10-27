import pytest

from pykd.record import (
    MAX_KEY_SIZE,
    MAX_VALUE_SIZE,
    RECORD_HEADER_SIZE,
    Record,
    RecordError,
    RecordType,
)


def test_record_creation():
    record = Record("name", "AK")

    assert record.key == "name"
    assert record.value == "AK"
    assert record.record_type == RecordType.SET
    assert record.is_set
    assert not record.is_delete


def test_key_bytes():
    record = Record("name", "AK")

    assert record.key_bytes == b"name"


def test_value_bytes():
    record = Record("name", "AK")

    assert record.value_bytes == b"AK"


def test_serialized_size():
    record = Record("name", "AK")

    expected = RECORD_HEADER_SIZE + 4 + 2

    assert record.serialized_size == expected


def test_serialize():
    record = Record("name", "AK")

    data = record.serialize()

    assert isinstance(data, bytes)
    assert len(data) == record.serialized_size


def test_serialize_and_deserialize():
    record = Record("name", "AK")

    data = record.serialize()
    restored = Record.deserialize(data)

    assert restored == record


def test_unicode_round_trip():
    record = Record("नाम", "आयुष")

    data = record.serialize()
    restored = Record.deserialize(data)

    assert restored.key == "नाम"
    assert restored.value == "आयुष"


def test_empty_value_is_allowed_for_set():
    record = Record("name", "")

    data = record.serialize()
    restored = Record.deserialize(data)

    assert restored.key == "name"
    assert restored.value == ""
    assert restored.is_set


def test_empty_key_is_rejected():
    with pytest.raises(ValueError):
        Record("", "value")


def test_non_string_key_is_rejected():
    with pytest.raises(TypeError):
        Record(123, "value")


def test_non_string_value_is_rejected():
    with pytest.raises(TypeError):
        Record("key", 123)


def test_null_character_in_key_is_rejected():
    with pytest.raises(ValueError):
        Record("na\x00me", "value")


def test_key_size_limit():
    key = "x" * MAX_KEY_SIZE

    record = Record(key, "value")

    assert len(record.key_bytes) == MAX_KEY_SIZE


def test_key_exceeding_size_limit():
    key = "x" * (MAX_KEY_SIZE + 1)

    with pytest.raises(RecordError):
        Record(key, "value")


def test_value_size_limit():
    value = "x" * MAX_VALUE_SIZE

    record = Record("key", value)

    assert len(record.value_bytes) == MAX_VALUE_SIZE


def test_value_exceeding_size_limit():
    value = "x" * (MAX_VALUE_SIZE + 1)

    with pytest.raises(RecordError):
        Record("key", value)


def test_deserialize_rejects_short_data():
    with pytest.raises(RecordError):
        Record.deserialize(b"short")


def test_deserialize_rejects_invalid_record_type():
    data = (
        (99).to_bytes(1, "big")
        + (1).to_bytes(4, "big")
        + (1).to_bytes(4, "big")
        + b"k"
        + b"v"
    )

    with pytest.raises(RecordError):
        Record.deserialize(data)


def test_deserialize_rejects_invalid_key_size():
    record = Record("name", "AK")
    data = bytearray(record.serialize())

    data[1:5] = (MAX_KEY_SIZE + 1).to_bytes(4, "big")

    with pytest.raises(RecordError):
        Record.deserialize(bytes(data))


def test_deserialize_rejects_invalid_value_size():
    record = Record("name", "AK")
    data = bytearray(record.serialize())

    data[5:9] = (MAX_VALUE_SIZE + 1).to_bytes(4, "big")

    with pytest.raises(RecordError):
        Record.deserialize(bytes(data))


def test_deserialize_rejects_wrong_total_size():
    record = Record("name", "AK")

    data = record.serialize() + b"extra"

    with pytest.raises(RecordError):
        Record.deserialize(data)


def test_deserialize_rejects_invalid_utf8():
    data = (
        RecordType.SET.to_bytes(1, "big")
        + (1).to_bytes(4, "big")
        + (1).to_bytes(4, "big")
        + b"\xff"
        + b"\xff"
    )

    with pytest.raises(RecordError):
        Record.deserialize(data)


def test_multiple_records_are_independent():
    record1 = Record("name", "AK")
    record2 = Record("age", "22")

    restored1 = Record.deserialize(record1.serialize())
    restored2 = Record.deserialize(record2.serialize())

    assert restored1 == record1
    assert restored2 == record2


def test_delete_record():
    record = Record.delete("name")

    assert record.key == "name"
    assert record.value == ""
    assert record.record_type == RecordType.DELETE
    assert record.is_delete
    assert not record.is_set


def test_delete_record_round_trip():
    record = Record.delete("name")

    data = record.serialize()
    restored = Record.deserialize(data)

    assert restored == record
    assert restored.is_delete


def test_delete_record_cannot_have_value():
    with pytest.raises(ValueError):
        Record(
            "name",
            "AK",
            RecordType.DELETE,
        )


def test_delete_record_serialized_size():
    record = Record.delete("name")

    assert record.serialized_size == (
        RECORD_HEADER_SIZE + len(b"name")
    )


def test_set_record_has_default_type():
    record = Record("name", "AK")

    assert record.record_type == RecordType.SET


def test_record_types_have_expected_values():
    assert RecordType.SET == 1
    assert RecordType.DELETE == 2