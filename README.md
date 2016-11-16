# Chat roulette python server

Chat roulette TCP server for practicing DH key exchange. Used in PV181 lectures on [FI MU].
For more information please see [JCA/JCE] page.

The purpose of the server is to interconnect connected clients and transparently route messages between them.
Each 30 seconds a new pairing epoch is started and each connected client gets paired with another one.

With this server, client can communicate with each other by exchanging JSON messages between each other
without need to have direct connection to end peers, server routes the communication between peers transparently.

## Protocol

The communication protocol is based on JSON. Each message is a JSON object, delimited by a new line character.
Each client registers to the server under an unique `UCO`.
It is some kind of identifier.

### Registration

P1 registers to the server by sending JSON

```json
{"cmd": "connect", "uco":"123456", "session":"1", "nonce":"123456"}
```

The response is

```json
{"ack": "123456"}
```

Then P2 registers in the same way, under uco `987654`.

### Pairing

In a new pairing window, server pairs P1 and P2 together. Both are notified about such event by a new message

```json
{"cmd": "pair", "uco": "987655"}
```

and P2 receives:

```json
{"cmd": "pair", "uco": "123456"}
```

### Communication

Then P1 and P2 can start communicating together by sending messages to the server like this:

```json
{"cmd": "comm", "uco":"123456", "session":"1", "nonce":"123456", "data":"test-test"}
```

This message was sent by P1, server delivers it as it is to P2. The `cmd` set to `comm` means it should be forwarded
to the paired peer.

In case of an error server sends error messages back, like the following:

```json
{"error": "no peer", "msg": {"cmd": "comm", "uco":"123456", "session":"1", "nonce":"123456", "data":"test-test"}}
```

### Ping pong

To make client database fresh, server sends a simple ping message to each connected client each second.

```json
{"cmd": "ping"}
```

The client is supposed to reply with the pong message

```json
{"cmd": "pong", "uco":"1234567", "session":"1", "nonce":"pingnonce0123"}
```

If the client is not responding for more than 7 seconds, or pipe is broken or TCP sending fails, the client is removed
from the active database and won't be selected in next pairing window.

### Example

Server view:

```
2016-11-17 00:06:28 phx.local __main__[28151] INFO client connected: ('127.0.0.1', 49854)
2016-11-17 00:06:28 phx.local __main__[28151] INFO New client registered, uco: 67
2016-11-17 00:06:34 phx.local __main__[28151] INFO client connected: ('127.0.0.1', 49856)
2016-11-17 00:06:34 phx.local __main__[28151] INFO New client registered, uco: 220
2016-11-17 00:06:34 phx.local __main__[28151] INFO Pairing 67 <-> 220
```


## Server start

```bash
python chroulette/main.py start
```

## Installation

```bash
pip install --upgrade --find-links=. .
```

or

```bash
python setup.py install
```

### Testing client

```bash
python client.py
```

[FI MU]: https://www.fi.muni.cz/
[JCA/JCE]: http://www.fi.muni.cz/~xklinec/java/index.html

