from typing import Any

from .object import find_type


def deserialize(data: bytes) -> Any:
    deserializer_id = data[:32]

    deserializer = find_type(deserializer_id)

    if not deserializer:
        raise ValueError(f"Cannot deserialize object of type {deserializer_id}")

    return deserializer.deserialize(data[32:])
