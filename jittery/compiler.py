
import ast
import json
import subprocess

from jittery.transformer import JSTransformer
from jittery.js import ast as js_ast

class CompileError(Exception): pass

class Compiler:
  def __init__(self, source, source_name=None):
    self.source = source
    self.source_name = source_name
    self.py_ast = ast.parse(self.source)
    self.js_ast = JSTransformer().visit(self.py_ast)

  def compile(self):
    json_ = json.dumps(self.js_ast, cls=js_ast.NodeJSONEncoder)
    result = subprocess.check_output(['node', 'js/jittery-codegen/index.js'])
