import argparse
import sys
import os
import re
import math
import types
import time
import errors
import random
import utils
import types
import base64
import json
import itertools
from datetime import datetime
from blessed import Terminal
from core import Core
import logging, coloredlogs


logger = logging.getLogger(__name__)
coloredlogs.install()


class Record(object):
    def __init__(self, *args, **kwargs):
        self.success_ctr = 0
        self.success_rounds = []
        self.failed_ctr = 0
        self.failed_rounds = []


class App(object):
    def __init__(self, *args, **kwargs):
        self.fname = 'client.err.log'
        self.db = {}

    def app_main(self):
        """
        Open file, parse JSON logs, pass for processing
        :return:
        """
        logger.info('Opening the file %s' % self.fname)
        with open(self.fname, 'r') as fh:
            lines = fh.readlines()

            # each record is a JSON record.
            records = []
            for line in lines:
                if line is None or len(line) == 0:
                    continue

                try:
                    js = json.loads(line)
                    if 'peer' not in js or 'utc' not in js or 'sub' not in js:
                        continue

                    # uco validity check, throws exception if invalid integer
                    uco = int(js['peer'])
                    records.append(js)
                except:
                    pass

            self.process(records)
            self.results()

    def prev_state_check(self, cur, prev, required):
        """
        Simple state checking, print warning if state mismatches
        :param cur:
        :param prev:
        :param required:
        :return:
        """
        if prev == required:
            return True
        else:
            logger.warning('Cur state: %s, required: %s, got: %s' % (cur, required, prev))
            return False

    def store_run(self, k, succ_round, was_success):
        """
        Stores particular run to the user database
        :param k:
        :param succ_round:
        :param was_success:
        :return:
        """
        uco_rec = None
        if k in self.db:
            uco_rec = self.db[k]
        else:
            uco_rec = Record()
            self.db[k] = uco_rec
        if was_success:
            uco_rec.success_ctr += 1
            uco_rec.success_rounds.append(succ_round)
        else:
            uco_rec.failed_ctr += 1
            uco_rec.failed_rounds.append(succ_round)

    def process(self, records):
        """
        Processing log records from the client.
        :param records:
        :return:
        """
        # quick & dirty approach - sort by (uco, time), follow uco thread (group by)
        records.sort(key=lambda x: (int(x['peer']), x['utc']))

        # quick and dirty group_by(peer) hack
        for k, g in itertools.groupby(records, key=lambda x: int(x['peer'])):
            # ignore invalid ranges
            if k < 111111 or k > 999999:
                continue

            logger.info('Processing UCO: %d' % k)

            state_ok = None  # False by default, wait for pair event.
            prev_state = None
            prev_hmac = None
            succ_round = []

            for msg in g:
                sub = msg['sub']
                evt = sub['evt']

                if evt == 'pair':
                    # previous state?
                    self.store_run(k, succ_round, state_ok and prev_state == 'finish')

                    succ_round = []
                    initiator = sub['initiator']
                    if not initiator:
                        logger.warning('Not an initiator: %s' % sub['connid'])
                        state_ok = False
                    else:
                        state_ok = True

                elif evt == 'dh1_send':
                    state_ok &= self.prev_state_check(evt, prev_state, 'pair')
                    if state_ok and not len(sub['dhpub']) > 100:
                        logger.warning('dhpub too short %s' % sub['dhpub'])
                        state_ok = False

                elif evt == 'dh1_recv':
                    state_ok = False

                elif evt == 'dh2_recv':
                    state_ok &= self.prev_state_check(evt, prev_state, 'dh1_send')
                    if state_ok and not len(sub['dhpub']) > 100:
                        logger.warning('dhpub too short %s' % sub['dhpub'])
                        state_ok = False

                    if state_ok and not sub['dhpub'].startswith('MII'):
                        logger.warning('dhpub has invalid prefix %s' % sub['dhpub'])
                        state_ok = False

                elif evt == 'dh2_send':
                    state_ok = False

                elif evt == 'dh_done':
                    state_ok &= self.prev_state_check(evt, prev_state, 'dh2_recv')
                    if state_ok and not len(sub['secret']) > 100:
                        logger.warning('secret is too short: %s' % sub['secret'])
                        state_ok = False

                elif evt == 'dhc_send':
                    state_ok &= self.prev_state_check(evt, prev_state, 'dh_done')
                    if state_ok and not len(sub['hmac']) > 20:
                        logger.warning('hmac is too short: %s' % sub['hmac'])
                        state_ok = False

                    prev_hmac = sub['hmac']

                elif evt == 'dhc_recv':
                    state_ok &= self.prev_state_check(evt, prev_state, 'dhc_send')
                    if state_ok and not len(sub['hmac']) > 20:
                        logger.warning('hmac is too short: %s' % sub['hmac'])
                        state_ok = False

                    if state_ok and sub['hmac'] != prev_hmac:
                        logger.warning('HMAC mismatch [%s] vs [%s]' % (prev_hmac, sub['hmac']))
                        state_ok = False

                elif evt == 'dhc_check':
                    state_ok &= self.prev_state_check(evt, prev_state, 'dhc_recv')
                    if not sub['matches']:
                        logger.warning('The check does not match')
                        state_ok = False

                elif evt == 'finish':
                    if prev_state != 'dhc_check':
                        logger.warning('Finish state without check, prev state=%s' % prev_state)
                        state_ok = False
                    elif not state_ok:
                        logger.warning('Finish but state is not OK')

                else:
                    logger.warning('Unrecognized event: %s' % evt)

                prev_state = evt
                succ_round.append(msg)

            # last final invalid round store
            self.store_run(k, succ_round, state_ok and prev_state == 'finish')

    def dump_round(self, rounds):
        for msg in rounds:
            tc = msg['utc'] / 1000.0
            dt = datetime.fromtimestamp(tc)
            sub = msg['sub']
            print('    %s evt: %s; msg: %s' % (dt, sub['evt'], json.dumps(sub)))

    def results(self):
        """
        Print out the results for UCOs
        :return:
        """
        for uco in self.db:
            rec = self.db[uco]
            print('UCO: %s' % uco)
            print('  failed protocol rounds:  %s' % (rec.failed_ctr))
            print('  success protocol rounds: %s' % (rec.success_ctr))

            if len(rec.success_rounds) > 0:
                print('  last successful round:')
                self.dump_round(rec.success_rounds[-1])

            if len(rec.failed_rounds) > 0:
                print(' -' * 40)
                print('  failed rounds ')
                prev_len = None
                big_first = sorted(rec.failed_rounds, key=lambda x: len(x), reverse=True)
                self.dump_round(big_first[0])

            print('')
            print('-'*80)


def main():
    app = App()
    app.app_main()


if __name__ == '__main__':
    main()
