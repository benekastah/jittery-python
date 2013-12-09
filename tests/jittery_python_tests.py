
from nose.tools import *
from jittery import compiler
import subprocess

def jseval(text, bare = True):
    jscode = compiler.compile(text, bare = bare)
    result = subprocess.check_output(["node", "--eval", jscode, "--print"])
    return result.decode("utf-8").strip()

def setup():
    pass

def teardown():
    pass

def test_basic():
    # Basic math operations
    assert jseval("1 + 1") == "2"
    assert jseval("1.45 * 1") == "1.45"
    assert jseval("-5 / 5") == "-1"

    compiler.compile(file = "tests/scripts/jsfile.py")
