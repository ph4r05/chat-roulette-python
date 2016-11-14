import socket
import threading
import SocketServer
import logging, coloredlogs
import json
import re
import queue


__author__ = 'dusanklinec'


logger = logging.getLogger(__name__)
coloredlogs.install()


class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):
    """
    Request handler
    """
    def __init__(self, request, client_address, server, *args, **kwargs):
        self.logger = logging.getLogger('EchoRequestHandler')
        self.logger.debug('__init__')
        self.server = server
        self.running = True
        self.queue = None
        self.data = None
        SocketServer.StreamRequestHandler.__init__(self, request, client_address, server)
        return

    def send_msg(self, msg):
        """
        Enqueues message for the sending
        """
        pass

    def try_send(self, dict):
        try:
            self.wfile.write(json.dumps(dict)+'\n')
            return 0
        except:
            return 1

    def terminate(self):
        self.running = False

    def handle(self):
        # logger.info('Server: %s master: %s' % (self.server, self.server.master))
        # socket: self.request
        server = self.server
        master = self.server.master
        self.request.settimeout(0.5)
        #logger.info('Client {} connected'.format(self.client_address))

        # Register here...
        master.on_connected(server, self, self.client_address, self.request, self.rfile, self.wfile)
        try:
            while self.running:
                try:
                    self.data = self.rfile.readline().strip()
                    if self.data is not None and len(self.data) > 0:
                        master.on_read(server, self, self.client_address, self.data)

                except socket.timeout:
                    # Timeout occurred, do things
                    pass

        except Exception as e:
            pass
        master.on_disconnected(server, self, self.client_address, self.request, self.rfile, self.wfile)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """
    The actual server
    """
    def __init__(self, server_address, handler_class, bind_now=True, wrapper=None, master=None, *args, **kwargs):
        self.logger = logging.getLogger('EchoServer')
        self.logger.debug('__init__')
        self.wrapper = wrapper
        self.master = master
        SocketServer.TCPServer.__init__(self, server_address, handler_class, bind_now)
        return
    pass


class MasterTCPServer(object):
    """
    Dummy TCP server bound on the specific socket.
    Server is started in a new thread so it does not block.
    """
    def __init__(self, address, master=None, *args, **kwargs):
        SocketServer.TCPServer.allow_reuse_address = True
        self.address = address
        self.server = ThreadedTCPServer(self.address, ThreadedTCPRequestHandler, False, wrapper=self, master=master)
        self.thread = None
        self.master = master

    def start(self):
        """
        Starts the server in the separate thread (async)
        :return:
        """
        self.server.allow_reuse_address = True
        self.server.server_bind()     # Manually bind, to support allow_reuse_address
        self.server.server_activate() #

        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.setDaemon(True)
        self.thread.start()
        return self

    def close(self):
        """
        Shuts down the server
        :return:
        """
        try:
            self.server.shutdown()
            self.server.server_close()
        except:
            pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        print('sending %s to %s' % (message, (ip, port)))
        sock.sendall(message)
        response = sock.recv(1024)
        print "Received: {}".format(response)
    finally:
        sock.close()


if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 4444

    server = MasterTCPServer((HOST, PORT))
    server.start()

    ip, port = 'localhost', 4444

    print "Server loop running in thread:"
    client(ip, port, "Hello World 1\n")
    client(ip, port, "Hello World 2\n")
    client(ip, port, "Hello World 3\n")

    server.close()



