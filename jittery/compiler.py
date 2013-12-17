
import ast
import json
import tempfile
import subprocess
import os

from jittery.transformer import JSTransformer
import jittery
import jittery.context
import jittery.js.ast as js_ast

def compile(*args, **kwargs):
  return Compiler(*args, **kwargs).compile()

class CompileError(Exception): pass

class Compiler:
  def __init__(self, source, module_name='__main__', package=None,
               source_name=None, bare=False):
    self.source = source
    self.source_name = source_name
    self.py_ast = ast.parse(self.source)
    self.context = jittery.context.ContextStack()
    self.js_ast = JSTransformer(
      module_name, self.context, package, bare=bare).visit(self.py_ast)

  def compile(self):
    package_dir = os.path.dirname(jittery.__file__)
    ast_json = json.dumps(self.js_ast, cls=js_ast.JSONEncoder, indent=2)
    # print(ast_json)
    stdin = tempfile.NamedTemporaryFile()
    stdin.write(ast_json.encode('utf-8'))
    stdin.seek(0)
    result = subprocess.check_output(
      ['node', '%s/js/jittery-codegen/index.js' % package_dir],
      stdin=stdin)
    return result.decode('utf-8')
