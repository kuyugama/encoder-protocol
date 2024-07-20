from socket import socket
from typing import Iterator, TypeVar

from .object import Object

T = TypeVar('T', bound=Object)


def prepare_message(message: bytes, length_size: int = 4) -> bytes:
    return len(message).to_bytes(length_size, byteorder="big") + message


def read_one(data: bytes, length_size: int = 4) -> bytes | None:
    if len(data) < length_size:
        return None

    length = int.from_bytes(data[:length_size], byteorder="big")
    return data[length_size : length + length_size]

def socket_read_one(socket: socket, length_size: int = 4) -> bytes | None:
    socket.settimeout(1)
    try:
        length_bytes = socket.recv(length_size)
        if not length_bytes:
            return None

        length = int.from_bytes(length_bytes, byteorder="big")

        return socket.recv(length)
    except TimeoutError:
        return None
    finally:
        socket.settimeout(1)


def read_iter(data: bytes, length_size: int = 4) -> Iterator[bytes]:
    while len(data) >= length_size:
        read = read_one(data, length_size)
        yield read
        data = data[length_size + len(read) :]


def socket_read_iter(socket: socket, length_size: int = 4) -> Iterator[bytes]:
    while (message := socket_read_one(socket, length_size)) is not None:
        yield message


def socket_read_all(socket: socket, length_size: int = 4) -> list[bytes]:
    return list(socket_read_iter(socket, length_size))


class Buffer:
    def __init__(self, data: bytes = b"", message_length_size: int = 4):
        self._data = data
        self._length_size = message_length_size
        self._cursor = 0

    def prepare(self, message: bytes) -> bytes:
        return prepare_message(message, self._length_size)

    def write(self, message: bytes | Object) -> int:
        if isinstance(message, Object):
            message = message.serialize()

        message = self.prepare(message)

        self._data += message

        return len(message)

    def write_many(self, *messages: bytes | Object) -> int:
        wrote = 0
        for message in messages:
            wrote += self.write(message)

        return wrote

    def read(self, type_: type[T] = None) -> bytes | T:
        read = read_one(self._data[self._cursor :], self._length_size)

        if read is not None:
            self._cursor += self._length_size + len(read)

        if type_ is not None:
            return type_.deserialize(read)

        return read

    def read_iter(self) -> Iterator[bytes]:
        for data in read_iter(self._data[self._cursor :], self._length_size):
            yield data
            self._cursor += self._length_size + len(data)

    def read_all(self) -> list[bytes]:
        return list(self.read_iter())

    def bytes(self) -> bytes:
        return self._data


class SocketBuffer:
    def __init__(self, socket: socket, message_length_size: int = 4):
        self._socket = socket
        self._message_length_size = message_length_size

    def prepare(self, message: bytes) -> bytes:
        return prepare_message(message, self._message_length_size)

    def write(self, message: bytes | Object) -> int:
        if isinstance(message, Object):
            message = message.serialize()

        message = self.prepare(message)

        return self._socket.send(message)

    def write_many(self, *messages: bytes | Object) -> int:
        wrote = 0

        for message in messages:
            wrote += self.write(message)

        return wrote

    def read(self, type_: type[T] = None) -> bytes | T:
        read = socket_read_one(self._socket, self._message_length_size)

        if type_ is not None:
            return type_.deserialize(read)

        return read

    def read_iter(self) -> Iterator[bytes]:
        yield from socket_read_iter(self._socket, self._message_length_size)

    def read_all(self) -> list[bytes]:
        return socket_read_all(self._socket, self._message_length_size)
