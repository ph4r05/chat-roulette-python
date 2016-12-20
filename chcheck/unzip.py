import argparse
import sys
import os
import re
import math
import types
import time
import random
import types
import base64
import json
import itertools
import zipfile
from datetime import datetime
from blessed import Terminal
from os import walk
import logging, coloredlogs


logger = logging.getLogger(__name__)
coloredlogs.install()


class App(object):
    def __init__(self, *args, **kwargs):
        self.args = None
        self.resdir = None
        self.srcdir = None
        self.zips = []

    def app_main(self):
        parser = argparse.ArgumentParser(description='Unzip all archives in the directory')

        parser.add_argument('--dir', dest='dir', default='unpack',
                            help='default directory for unpacking')

        parser.add_argument('zipdir', nargs=argparse.ZERO_OR_MORE, default=[],
                            help='directories with ZIP files to unpack')

        self.args = parser.parse_args()
        self.resdir = self.args.dir
        self.srcdir = self.args.zipdir[0]

        # analyze source dir
        for (dirpath, dirnames, filenames) in walk(self.srcdir):
            for filename in filenames:
                if not filename.lower().endswith('.zip'):
                    continue
                self.zips.append(os.path.join(dirpath, filename))
            break

        self.unzip()

    def unzip(self):
        for zip_file in self.zips:
            basename = os.path.basename(zip_file)
            dir_name = basename.rsplit('.', 1)[0]
            dest_dir = os.path.join(self.resdir, dir_name)

            logger.info('Unzipping %s dir: %s' % (zip_file, dest_dir))
            zf = zipfile.ZipFile(zip_file)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            zf.extractall(path=dest_dir)
        pass


def main():
    app = App()
    app.app_main()


if __name__ == '__main__':
    main()
