
import json
import subprocess

from nose.tools import *

from jittery import compiler

def jseval(text, bare = True):
  jscode = compiler.compile(text, bare = bare)
  result = subprocess.check_output(["node", "--eval", jscode, "--print"])
  return result.decode("utf-8").strip()

def identity(x):
  return x

def expressionify(tp, autotyped=False):
  l = len(tp)
  if l == 3:
    return tp
  elif l == 2:
    return tp + (identity if not autotyped else type(tp[1]),)
  else:
    raise Exception('Invalid expression format')

def expressions(autotyped=False):
  def wrapper(fn):
    def wrapper2():
      exprs = fn()
      for entry in exprs:
        code, expected, converter = expressionify(entry, autotyped)
        answer = converter(jseval(code))
        assert answer == expected, \
          'evaluating "%s": expecting %s but got %s' % \
          (code, json.dumps(expected), json.dumps(answer))
    wrapper2.__name__ = fn.__name__
    return wrapper2
  return wrapper

def setup():
  pass

def teardown():
  pass

@expressions(autotyped=True)
def test_basic_math():
  return (
    ('1 + 1', 2),
    ('3 - 1', 2),
    ('1.45 * 1', 1.45),
    ('-5 / 5', -1),
    ('5 / 2', 2.5),
    ('5 // 2', 2),
    ('5 ** 2', 25),
    ('5 % 2', 1),
    ('5 * 3 + 1', 16),
    ('5 * (3 + 1)', 20),
  )

@expressions(autotyped=True)
def test_bitwise_operations():
  return (
    ('1 ^ 1', 0),
    ('5 ^ 3', 6),
    ('1 << 3', 8),
    ('100 >> 3', 12),
    ('2 | 4', 6),
    ('~5', -6),
    ('~~5.6', 5),
    ('4 & 2', 0),
  )

@expressions()
def test_strings():
  return (
    ("'asdf'", 'asdf'),
    ('"asdf"', 'asdf'),
    ('"asdf" + "fdsa"', 'asdffdsa'),
    # ('"%s!" % \'froot\'', 'froot!')
  )

def test_functions():
  code = """
def factorial(n):
  if n is 0:
    return 1
  else:
    return n * factorial(n - 1)

factorial(5)
  """
  assert int(jseval(code)) == 5
