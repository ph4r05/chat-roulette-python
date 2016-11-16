from cmd2 import Cmd
import argparse
import sys
import os
import re
import math
import types
import traceback
import pid
import time
import textwrap
import errors
import random
import utils
import types
import base64
import json
import datetime
from blessed import Terminal
from core import Core
import logging, coloredlogs
import server
from threading import Thread


logger = logging.getLogger(__name__)
coloredlogs.install()


class Client(object):
    """
    Client record holder.
    Stores information about connected client.
    """
    def __init__(self, handler=None, uco=None, session=None, *args, **kwargs):
        self.handler = handler
        self.uco = uco
        self.client = handler.client_address
        self.session = session
        self.peer = None
        self.dead = False
        self.last_pong = -1.0

    def unpair(self):
        """
        Bidirectional pairing cancellation.
        :return:
        """
        try:
            if self.peer is not None:
                self.peer.peer = None
        except:
            pass
        self.peer = None

    def check_peer(self):
        """
        If remote peer is dead, deassociate.
        :return:
        """
        try:
            if self.peer is not None and self.peer.dead:
                self.peer = None
                self.peer.peer = None
        except:
            pass



class App(Cmd):
    """Chat roulette command line interface"""
    prompt = '$> '

    PIP_NAME = 'chat-roulette-server'
    PROCEED_YES = 'yes'
    PROCEED_NO = 'no'
    PROCEED_QUIT = 'quit'

    def __init__(self, *args, **kwargs):
        """
        Init core
        :param args:
        :param kwargs:
        :return:
        """
        Cmd.__init__(self, *args, **kwargs)
        self.core = Core()
        self.args = None
        self.last_result = 0
        self.last_n_logs = 5

        self.noninteractive = False
        self.version = 'trunk'
        self.hide_key = True
        self.root_required = False

        self.t = Terminal()
        self.update_intro()

        self.server = server.MasterTCPServer(('0.0.0.0', 44333), master=self)
        self.client_db = {}
        self.running = True
        self.pinger_thread = None
        self.assoc_thread = None

    def update_intro(self):
        self.intro = '-'*self.get_term_width() + \
                     ('\n    Chat roulette command line interface (v%s) \n' % self.version) + \
                     '\n    usage - shows simple command list'

        self.intro += '\n    More info: https://google.com \n' + \
                      '-'*self.get_term_width()

    def do_version(self, line):
        print('%s-%s' % (self.PIP_NAME, self.version))

    def do_usage(self, line):
        """Simple usage info"""
        print('start  - starts the server')
        print('stop   - stops the server')
        print('usage  - writes this usage info')

    def do_start(self, line):
        """
        Start the TCP server and management threads
        :param line:
        :return:
        """
        self.running = True
        self.server.start()

        self.pinger_thread = Thread(target=self.pinger, args=())
        self.pinger_thread.start()

        self.assoc_thread = Thread(target=self.assoc, args=())
        self.assoc_thread.start()

        logger.info('Server started')

    def do_stop(self, line):
        """
        Stops the running server and management threads.
        :param line:
        :return:
        """
        self.running = False
        self.server.close()
        logger.info('Server stopped')

    def pinger(self):
        """
        Main pinger worker method. Pings each connected client each second.
        :return:
        """
        while self.running:
            cls = self.client_db.items()
            for tup in cls:
                cl = tup[1]
                if cl.dead:
                    continue
                cl.handler.try_send({'cmd':'ping'})
            time.sleep(1.0)

    def assoc(self):
        """
        Main association worker method.
        Takes care about the client list and re-associations.
        :return:
        """
        last_reassoc = 0.0
        while self.running:
            cur_time = time.time()
            cls = self.client_db.items()

            # Maintenance
            for tup in cls:
                cl = tup[1]

                if cl.last_pong > 0.0 and cur_time - cl.last_pong > 7.0 and not cl.dead:
                    logger.info('Making client dead: %s' % cl.uco)
                    cl.dead = True

                if cl.dead:
                    cl.unpair()
                    continue

                cl.check_peer()

            if cur_time - last_reassoc > 30.0:
                for tup in cls:
                    cl = tup[1]
                    cl.unpair()
                last_reassoc = cur_time
                continue

            # Pairing of new peers
            # a) get list of free ones
            free_peers = []
            for tup in cls:
                cl = tup[1]
                if cl.peer is None and not cl.dead:
                    free_peers.append(cl)

            while len(free_peers) >= 2:
                p1 = random.choice(free_peers)
                free_peers.remove(p1)

                p2 = random.choice(free_peers)
                free_peers.remove(p2)

                self.pair_peers(p1, p2)

            time.sleep(0.5)

    def pair_peers(self, p1, p2):
        """
        Utility method for pairing p1 and p2.
        Each peer is notified about this event by a new message
        :param p1:
        :param p2:
        :return:
        """
        logger.info('Pairing %s <-> %s ' % (p1.uco, p2.uco))
        p1.peer = p2
        p2.peer = p1
        try:
            p1.handler.try_send({'cmd': 'pair', 'uco': p2.uco})
            p2.handler.try_send({'cmd': 'pair', 'uco': p1.uco})
        except Exception as e:
            logger.error('Exception in pairing %s <-> %s: %s' % (p1.uco, p2.uco, e))
            p1.peer = None
            p2.peer = None

    def on_connected(self, server, handler, client=None, socket=None, rfile=None, wfile=None):
        """
        Called by the server handler when new client connects
        :param server:
        :param handler:
        :param client:
        :param socket:
        :param rfile:
        :param wfile:
        :return:
        """
        logger.info('client connected: %s' % str(client))

    def on_disconnected(self, server, handler, client=None, socket=None, rfile=None, wfile=None):
        """
        Called by the server handler when client disconnects
        :param server:
        :param handler:
        :param client:
        :param socket:
        :param rfile:
        :param wfile:
        :return:
        """
        for tup in self.client_db.items():
            cl = tup[1]
            if cl.client == client:
                cl.dead = True
                logger.info('Client %s disconnected' % cl.uco)
                return

        logger.info('disconnected: %s' % str(client))

    def on_read(self, server, handler, client, data):
        """
        Called by the server handler when a new message is received from the client.
        :param server:
        :param handler:
        :param client:
        :param data:
        :return:
        """
        socket, rfile, wfile = handler.request, handler.rfile, handler.wfile
        try:
            if len(data) > 32768:
                handler.try_send({'error': 'message too long'})
                return

            # Load json message from the received data
            js = json.loads(data)

            if 'cmd' not in js:
                logger.info('parsed: %s' % js)
                return

            cmd = str(js['cmd'])
            uco = str(js['uco'])[:24]
            session = str(js['session'])[:24]
            nonce = str(js['nonce'])[:24]

            # uco sanitization
            uco = ''.join(e for e in uco if e.isalnum())

            if cmd == 'connect':
                client = Client(handler=handler, uco=uco, session=session)
                if uco in self.client_db:
                    cl = self.client_db[uco]

                    # terminate all the time - multiple instances...
                    self.terminate_client(self.client_db[uco])

                    # if cl.client != client.client:
                    #    self.terminate_client(self.client_db[uco])

                self.client_db[uco] = client
                handler.try_send({'ack': nonce})

                logger.info('New client registered, uco: %s' % uco)

                # Try to find a peer... If there is any
                # contact both peers then... inform they are connected together...

            elif cmd == 'exit':
                if uco in self.client_db:
                    self.terminate_client(self.client_db[uco])

            elif cmd == 'comm':
                if uco in self.client_db:
                    cl = self.client_db[uco]
                    if cl.peer is None:
                        handler.try_send({'error': 'no peer', 'msg': js})
                    else:
                        try:
                            cl.peer.handler.try_send(js)
                        except:
                            handler.try_send({'error': 'failed', 'msg': js})

            elif cmd == 'pong':
                if uco in self.client_db:
                    cl = self.client_db[uco]
                    cl.dead = False
                    cl.last_pong = time.time()

            else:
                handler.try_send({'error': 'Unknown command [%s]' % cmd})
                logger.info('parsed: %s' % js)

        except Exception as e:
            logger.warning('Parsing exception: %s' % e)
            handler.try_send({'exit': True})
            handler.terminate()

    def terminate_client(self, client):
        """
        Helper method for terminating clients connection.
        :param client:
        :return:
        """
        try:
            if client is None or client.dead:
                return
            client.handler.try_send({'exit': True, 'reason': 'new session'})
            client.handler.terminate()
            client.dead = True
        except:
            pass

    def return_code(self, code=0):
        self.last_result = code
        return code

    def cli_sleep(self, iter=5):
        for lines in range(iter):
            print('')
            time.sleep(0.1)

    def ask_proceed_quit(self, question=None, support_non_interactive=False, non_interactive_return=PROCEED_YES, quit_enabled=True):
        """Ask if user wants to proceed"""
        opts = 'Y/n/q' if quit_enabled else 'Y/n'
        question = question if question is not None else ('Do you really want to proceed? (%s): ' % opts)

        if self.noninteractive and not support_non_interactive:
            raise errors.Error('Non-interactive mode not supported for this prompt')

        if self.noninteractive and support_non_interactive:
            if self.args.yes:
                print(question)
                if non_interactive_return == self.PROCEED_YES:
                    print('Y')
                elif non_interactive_return == self.PROCEED_NO:
                    print('n')
                elif non_interactive_return == self.PROCEED_QUIT:
                    print('q')
                else:
                    raise ValueError('Unknown default value')

                return non_interactive_return
            else:
                raise errors.Error('Non-interactive mode for a prompt without --yes flag')

        # Classic interactive prompt
        confirmation = None
        while confirmation != 'y' and confirmation != 'n' and confirmation != 'q':
            confirmation = raw_input(question).strip().lower()
        if confirmation == 'y':
            return self.PROCEED_YES
        elif confirmation == 'n':
            return self.PROCEED_NO
        else:
            return self.PROCEED_QUIT

    def ask_proceed(self, question=None, support_non_interactive=False, non_interactive_return=True):
        """Ask if user wants to proceed"""
        ret = self.ask_proceed_quit(question=question,
                                    support_non_interactive=support_non_interactive,
                                    non_interactive_return=self.PROCEED_YES if non_interactive_return else self.PROCEED_NO,
                                    quit_enabled=False)

        return ret == self.PROCEED_YES

    def check_pid(self, retry=True):
        """Checks if the tool is running"""
        first_retry = True
        attempt_ctr = 0
        while first_retry or retry:
            try:
                first_retry = False
                attempt_ctr += 1

                self.core.pidlock_create()
                if attempt_ctr > 1:
                    print('\nPID lock acquired')
                return True

            except pid.PidFileAlreadyRunningError as e:
                return True

            except pid.PidFileError as e:
                pidnum = self.core.pidlock_get_pid()
                print('\nError: CLI already running in exclusive mode by PID: %d' % pidnum)

                if self.args.pidlock >= 0 and attempt_ctr > self.args.pidlock:
                    return False

                print('Next check will be performed in few seconds. Waiting...')
                time.sleep(3)
        pass

    def get_term_width(self):
        try:
            width = self.t.width
            if width is None or width <= 0:
                return 80

            return width
        except:
            pass
        return 80

    def wrap_term(self, text="", single_string=False, max_width=None):
        width = self.get_term_width()
        if max_width is not None and width > max_width:
            width = max_width

        res = textwrap.wrap(text, width)
        return res if not single_string else '\n'.join(res)

    def app_main(self):
        # Backup original arguments for later parsing
        args_src = sys.argv

        # Parse our argument list
        parser = argparse.ArgumentParser(description='Chat roulette python server')
        parser.add_argument('-n', '--non-interactive', dest='noninteractive', action='store_const', const=True,
                            help='non-interactive mode of operation, command line only')
        parser.add_argument('-r', '--attempts', dest='attempts', type=int, default=3,
                            help='number of attempts in non-interactive mode')
        parser.add_argument('-l','--pid-lock', dest='pidlock', type=int, default=-1,
                            help='number of attempts for pidlock acquire')
        parser.add_argument('--debug', dest='debug', action='store_const', const=True,
                            help='enables debug mode')
        parser.add_argument('--verbose', dest='verbose', action='store_const', const=True,
                            help='enables verbose mode')
        parser.add_argument('--force', dest='force', action='store_const', const=True, default=False,
                            help='forces some action')

        parser.add_argument('commands', nargs=argparse.ZERO_OR_MORE, default=[],
                            help='commands to process')

        self.args = parser.parse_args(args=args_src[1:])
        self.noninteractive = self.args.noninteractive

        # Fixing cmd2 arg parsing, call cmdLoop
        sys.argv = [args_src[0]]
        for cmd in self.args.commands:
            sys.argv.append(cmd)

        # Terminate after execution is over on the non-interactive mode
        if self.noninteractive:
            sys.argv.append('quit')

        if self.args.debug:
            coloredlogs.install(level=logging.DEBUG)

        self.cmdloop()
        sys.argv = args_src

        # Noninteractive - return the last result from the operation (for scripts)
        if self.noninteractive:
            sys.exit(self.last_result)


def main():
    app = App()
    app.app_main()


if __name__ == '__main__':
    main()
