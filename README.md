# Chat roulette python server

Chat roulette server for practicing DH key exchange. Used in PV181 lectures on [FI MU].
For more information please see [JCA/JCE] page.

The purpose of the server is to interconnect connected clients and transparently route messages between them.
Each 30 seconds a new pairing epoch is started and each connected client gets paired with another one.

The communication protocol is based on JSON.

## Start

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

