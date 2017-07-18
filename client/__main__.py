import sys

from . import parser

# with open('runtime/builtins.py') as t:
#     print(parser.to_js(t.read()))

with open('test/test.py') as t:
    print(parser.to_js(t.read()))
