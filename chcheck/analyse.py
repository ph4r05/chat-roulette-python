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
from os import walk, listdir
import logging
import coloredlogs
import editdistance
from shutil import copyfile


logger = logging.getLogger(__name__)
coloredlogs.install()


class App(object):
    def __init__(self, *args, **kwargs):
        self.args = None
        self.rootdir = None
        self.mossdir = None
        self.filename = None

        self.filedb = {}
        self.file_data = {}

    def app_main(self):
        parser = argparse.ArgumentParser(description='Compare files')

        parser.add_argument('--root', dest='rootdir',
                            help='rootdir to start with')

        parser.add_argument('--moss', dest='mossdir',
                            help='Builds moss directory structure')

        parser.add_argument('--file', dest='filename',
                            help='filename to look for in the archive')

        self.args = parser.parse_args()
        self.rootdir = self.args.rootdir
        self.filename = self.args.filename
        if self.args.mossdir is not None:
            self.mossdir = self.args.mossdir

        self.find()
        self.mossdirs()

        # Finding similarities - Levenshtein edit distance.
        # self.similarities()

    def find(self):
        """
        Finds UCO -> target file mapping in the subdirectories
        :return:
        """

        fname_to_find = self.filename.lower()
        subdirs = [f for f in listdir(self.rootdir) if os.path.isdir(os.path.join(self.rootdir, f))]
        for subdir in subdirs:
            matches = re.match('^([0-9]+).*', subdir)
            if not matches:
                logger.error('Directory %s did not match UCO criteria' % (subdir))
                continue

            uco = int(matches.group(1))
            logger.info('Processing results for %s, directory: %s' % (uco, subdir))

            cdir = os.path.join(self.rootdir, subdir)

            # find the specified file
            file_path = None
            for (dirpath, dirnames, filenames) in walk(cdir):
                for filename in filenames:
                    if fname_to_find == filename.lower():
                        file_path = os.path.join(dirpath, filename)

            if not file_path:
                logger.warning('File %s was not found in %s' % (self.filename, cdir))
                continue

            logger.info('Got the file: %s' % file_path)
            self.filedb[uco] = file_path

            with open(file_path, 'r') as fh:
                self.file_data[uco] = fh.read()

    def mossdirs(self):
        """
        Builds directory structure for http://theory.stanford.edu/~aiken/moss/
        if user entered the moss directory
        :return:
        """
        if self.mossdir is None:
            return

        if not os.path.exists(self.mossdir):
            os.makedirs(self.mossdir)

        for uco in self.filedb:
            filename = self.filedb[uco]
            ucodir = os.path.join(self.mossdir, str(uco))
            dest_file = os.path.join(ucodir, os.path.basename(filename))

            if not os.path.exists(ucodir):
                os.makedirs(ucodir)
            copyfile(filename,  dest_file)

    def similarities(self):
        """
        Compute Levenshtein distance matrix between files (implemented in C++ pip package: editdistance)
        Later: https://docs.python.org/2/library/difflib.html
        :return:
        """

        ucos = sorted(self.filedb.keys())
        sims = {}

        for idx, uco in enumerate(ucos):
            logger.info('Comparing %s...' % uco)
            sims[uco] = {}

            for idx2, uco2 in enumerate(ucos[idx+1:]):
                dist = editdistance.eval(self.file_data[uco], self.file_data[uco2])
                sims[uco][uco2] = dist
                logger.info(' %6d vs %6d : %4d  %s  %s' % (uco, uco2, dist, self.filedb[uco], self.filedb[uco2]))

def main():
    app = App()
    app.app_main()


if __name__ == '__main__':
    main()
