from contextlib import contextmanager
import argparse
import ast
import os
import re
import sys

from . import parser
from .builder import parse_expr

DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

argparser = argparse.ArgumentParser(description='Compile python to javascript, sloppily')
argparser.add_argument('-s', '--source', dest='source', action='store', default=None,
                       help='A file or directory tree to compile')
argparser.add_argument('-o', '--outfile', dest='outfile', action='store',
                       default=None, help='The file to write to javascript to')

args = argparser.parse_args()

outfile = open(args.outfile, 'w') if args.outfile else sys.stdout


def validate_module_name(module_name):
    expr = parse_expr(module_name)
    for body in ast.walk(expr):
        assert isinstance(body, (ast.Name, ast.Attribute, ast.Load))


def get_modules(*package_dirs, extension='.py'):
    for package_dir in package_dirs:
        package_dir = os.path.join(package_dir, '')
        for dirpath, _, filenames, _ in os.fwalk(package_dir):
            for filename in filenames:
                if filename.endswith(extension):
                    filename = os.path.join(dirpath, filename)
                    module_name = filename[len(package_dir):-len(extension)]
                    module_name = re.sub(r'/', '.', module_name)
                    try:
                        validate_module_name(module_name)
                        yield filename, module_name
                    except AssertionError:
                        print('File {} cannot be used as a module (invalid name)'.format(filename))
                        raise


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
    for filename, modname in get_modules(os.path.join(DIR, 'runtime'), source):
        parser.to_js(filename, modname, outfile)
