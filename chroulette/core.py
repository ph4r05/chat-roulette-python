import json
import os.path
import pid
from datetime import datetime


class Core(object):
    def __init__(self, *args, **kwargs):
        """Init the core functions"""
        self.pidlock = pid.PidFile(pidname='chat-roulette-pv181.pid', piddir='/tmp')
        self.pidlock_created = False

    def pidlock_create(self):
        if not self.pidlock_created:
            self.pidlock.create()
            self.pidlock_created = True

    def pidlock_check(self):
        return self.pidlock.check()

    def pidlock_get_pid(self):
        filename = self.pidlock.filename
        if filename and os.path.isfile(filename):
            try:
                with open(filename, "r") as fh:
                    fh.seek(0)
                    pid = int(fh.read().strip())
                    return pid
            except:
                pass

        return None


