import types
import math
from datetime import datetime, date

from .object import Object
from .buffer import Buffer
from .serialize import serialize
from .deserialize import deserialize

class Str(Object, str):
    __synonyms__ = {str}

    def serialize(self) -> bytes:
        return self.encode("utf8")

    @classmethod
    def deserialize(cls, data: bytes) -> "Str":
        return cls(data.decode("utf8"))


class NoneType(Object):
    __synonyms__ = {types.NoneType}

    def serialize(self) -> bytes:
        return b""

    @classmethod
    def deserialize(cls, data: bytes) -> None:
        return None


class Boolean(Object, int):
    __synonyms__ = {bool}

    def serialize(self) -> bytes:
        return b"1" if self else b""

    @classmethod
    def deserialize(cls, data: bytes) -> "Boolean":
        return cls(bool(data))

    def __repr__(self) -> str:
        return "True" if self else "False"

    __str__ = __repr__


class Int(Object, int):
    __synonyms__ = {int}

    def serialize(self) -> bytes:
        # Convert to binary > get length of bits > split by 8 (bytes) > ceil result
        length = math.ceil(len(bin(self)[2:]) / 8)
        return self.to_bytes(length, "little")

    @classmethod
    def deserialize(cls, data: bytes) -> "Int":
        return cls(int.from_bytes(data, "little"))


class Bytes(Object, bytes):
    __synonyms__ = {bytes}

    def serialize(self) -> bytes:
        return self

    @classmethod
    def deserialize(cls, data: bytes) -> "Bytes":
        return cls(data)


class Float(Object, float):
    __synonyms__ = {float}

    def serialize(self) -> bytes:
        buffer = Buffer()

        parts = str(self).split(".")

        exp = Int(len(parts[1]))
        exp_bytes = exp.serialize()

        real = Int("".join(parts))
        real_bytes = real.serialize()

        buffer.write_many(exp_bytes, real_bytes)

        return buffer.bytes()

    @classmethod
    def deserialize(cls, data: bytes) -> "Float":
        buffer = Buffer(data)
        exp_bytes = buffer.read()
        real_bytes = buffer.read()

        exp = 10 ** int.from_bytes(exp_bytes, "little")
        real = int.from_bytes(real_bytes, "little")

        return real / exp


class List(Object, list):
    __synonyms__ = {list}

    def serialize(self) -> bytes:
        buffer = Buffer()

        for element in self:
            buffer.write(serialize(element))

        return buffer.bytes()

    @classmethod
    def deserialize(cls, data: bytes) -> "List":
        buffer = Buffer(data)
        elements = []

        for element in buffer.read_iter():
            elements.append(deserialize(element))

        return cls(elements)


class Dict(Object, dict):
    __synonyms__ = {dict}

    def serialize(self) -> bytes:
        buffer = Buffer()

        for key in self.keys():
            buffer.write(serialize(key))
            buffer.write(serialize(self[key]))

        return buffer.bytes()

    @classmethod
    def deserialize(cls, data: bytes) -> "Dict":
        buffer = Buffer(data)

        elements = {}

        while key := buffer.read():
            elements[deserialize(key)] = deserialize(buffer.read())

        return cls(elements)


class DateTime(Object, datetime):
    __synonyms__ = {datetime}

    def serialize(self):
        return Float(self.timestamp()).serialize()

    @classmethod
    def deserialize(cls, data: bytes) -> "DateTime":
        return cls.fromtimestamp(Float.deserialize(data))


class Date(Object, date):
    __synonyms__ = {date}

    def serialize(self) -> bytes:
        buffer = Buffer()
        buffer.write(Int(self.year))
        buffer.write(Int(self.month))
        buffer.write(Int(self.day))
        return buffer.bytes()

    @classmethod
    def deserialize(cls, data: bytes) -> "Date":
        buffer = Buffer(data)
        return cls(
            buffer.read(Int),
            buffer.read(Int),
            buffer.read(Int),
        )
