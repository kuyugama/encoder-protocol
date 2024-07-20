from abc import abstractmethod
from itertools import count
import hashlib
import typing

_types: set["type[Object]"] = set()
_synonyms: dict[type, "type[Object]"] = {}

_next_id = iter(count(1))
T = typing.TypeVar("T", bound="Object")


def is_abstract_method(method) -> bool:
    return getattr(method, "__isabstractmethod__", False)


class IdField:
    def __init__(self, value: bytes):
        self.__value = value

    def __get__(self, instance, owner):
        return self.__value


class ObjectMeta(type):
    def __new__(cls: type[T], name, bases, attrs):
        id = hashlib.sha256(name.encode()).digest()
        attrs["id"] = id

        for t in _types:
            if t.id == id:
                raise NameError("Type with this name already exists")

        type_ = type.__new__(cls, name, bases, attrs)

        _types.add(type_)
        _synonyms.update(
            {
                synonym: type_
                for synonym in getattr(type_, "__synonyms__", set())
            }
        )

        return type_

    def __call__(cls: type[T], *args, **kwargs):

        if is_abstract_method(cls.serialize) or is_abstract_method(
            cls.deserialize
        ):
            raise NotImplementedError(
                "serialize and deserialize methods should be implemented in Object subclasses to create instance"
            )

        return type.__call__(cls, *args, **kwargs)


class Object(metaclass=ObjectMeta):
    id: bytes
    __synonyms__: set[type]

    @abstractmethod
    def serialize(self: T) -> bytes:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def deserialize(cls: type[T], data: bytes) -> T:
        raise NotImplementedError


def find_type(cls: type | bytes) -> type[Object]:
    if isinstance(cls, bytes):
        for obj in _types:
            if obj.id == cls:
                return obj

    if cls in _synonyms:
        return _synonyms[cls]

    if cls in _types:
        return typing.cast(type[Object], cls)
