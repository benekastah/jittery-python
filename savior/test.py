"""Run the tests"""

import importlib
import os
import subprocess
import sys
import unittest

from savior import util

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
TEST_DIR = os.path.join(BASE_DIR, 'test_files')


def proc(cmd, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 3
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          encoding='UTF-8', **kwargs)


def make_test_class(filename):
    if filename == __file__:
        return
    module_name = util.get_module_name(os.path.dirname(TEST_DIR), filename)
    module = importlib.import_module(module_name)

    class ProcessTestCase(unittest.TestCase):
        __doc__ = module.__doc__

    def setUp(self):
        self.proc_py = proc([sys.executable, filename])
        proc_compile = proc([sys.executable, os.path.join(BASE_DIR, 'savior'), os.path.join(TEST_DIR, filename)])
        self.assertEqual(0, proc_compile.returncode, proc_compile.stderr)
        self.proc_js = proc(['nodejs'], input=proc_compile.stdout)

    def test_stdout(self):
        self.assertMultiLineEqual(self.proc_py.stdout, self.proc_js.stdout)

    def test_stderr(self):
        self.assertMultiLineEqual(self.proc_py.stderr, self.proc_js.stderr)

    def test_returncode(self):
        self.assertEqual(self.proc_py.returncode, self.proc_js.returncode)

    class_name = '.'.join(module_name.split('_'))
    class_name = ''.join(word.title() for word in class_name.split('.'))
    globals()[class_name] = type(class_name, (unittest.TestCase,), {
        '__doc__': module.__doc__,
        'setUp': setUp,
        'test_stdout': test_stdout,
        'test_stderr': test_stderr,
        'test_returncode': test_returncode
    });


def make_classes():
    for f in util.find_files(TEST_DIR):
        make_test_class(f)


make_classes()
