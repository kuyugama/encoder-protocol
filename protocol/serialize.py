from typing import Any

from .object import find_type


def serialize(value: Any) -> bytes:
    serializer = find_type(type(value))

    if not serializer:
        raise ValueError(f"Cannot serialize object of type {type(value)}")

    data = serializer.id + serializer.serialize(value)

    return data