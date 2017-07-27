from contextlib import contextmanager
import argparse
import ast
import os
import re
import sys

from savior import parser
from savior import util

DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

argparser = argparse.ArgumentParser(description='Compile python to javascript, sloppily')
argparser.add_argument('source', type=str,
                       help='A file or directory tree to compile')
argparser.add_argument('-o', '--outfile', dest='outfile', action='store',
                       default=None, help='The file to write to javascript to')

args = argparser.parse_args()


@contextmanager
def maybe_open(fname, *args, default=None):
    if fname:
        with open(fname, *args) as f:
            yield f
    else:
        yield default


with maybe_open(args.outfile, 'w', default=sys.stdout) as outfile:
    source = os.path.abspath(args.source)
    with open(os.path.join(DIR, 'runtime/bootstrap.js')) as bootstrap:
        outfile.write(bootstrap.read())
        outfile.write('\n')
    for filename, modname in util.get_modules(os.path.join(DIR, 'runtime'), source):
        parser.to_js(filename, modname, outfile)
