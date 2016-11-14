import socket
import threading
import SocketServer
import logging, coloredlogs
import json
import re
import queue
import random
import json

__author__ = 'dusanklinec'

def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    uco = random.randrange(0, 500, 1)
    try:
        sock.sendall(json.dumps({"cmd": "connect", "uco":uco, "session":1, "nonce":"123456"})+'\n')
        sock.settimeout(0.5)
        while True:
            try:
                response = sock.recv(4096)
                lines = response.split('\n')
                for line in lines:
                    if len(line) == 0:
                        continue
                    print "Received: {}".format(line)
                    js = json.loads(line)

                    if 'cmd' in js:
                        cmd = js['cmd']
                        if cmd == 'ping':
                            sock.sendall(json.dumps({"cmd": "pong", "uco":uco, "session":1, "nonce":"123456"})+'\n')

            except socket.timeout:
                pass


    finally:
        sock.close()


if __name__ == "__main__":
    ip, port = 'localhost', 44333
    client(ip, port, "Hello World 3\n")





