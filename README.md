# Encoder-Protocol

## Client-side
```python
import protocol
import socket
import math


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 19991))

data = protocol.serialize(123)

buffer = protocol.SocketBuffer(client, message_length_size=8)

buffer.write(data)

buffer.write_many(
    protocol.types.List([1, 2.0, "3", b"4", True, False]),
    protocol.types.Dict({1: 2, 3.0: 4, "5": 6, b"7": 8, True: False}),
    protocol.types.Float(math.pi),
)
```

## Server-side


```python
import protocol
import socket
import math

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 19991))

server.listen()

client, _addr = server.accept()

buffer = protocol.SocketBuffer(client, message_length_size=8)

data = protocol.deserialize(buffer.read())
assert data == 123

assert buffer.read(protocol.types.List) == [1, 2.0, "3", b"4", True, False]

assert buffer.read(protocol.types.Dict) == {
    1: 2,
    3.0: 4,
    "5": 6,
    b"7": 8,
    True: False,
}

assert buffer.read(protocol.types.Float) == math.pi
```