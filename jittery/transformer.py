
import ast
import copy

from jittery.js import ast as js_ast

class MagicPyAST(ast.AST):
  """Aggregates changes to AST instance without modifying the original
  """
  __reserved_names__ = ('__ast__', '__reserved_names__')

  def __init__(self, ast):
    self.__ast__ = ast

  def __getattribute__(self, name):
    if name in object.__getattribute__(self, '__reserved_names__'):
      return object.__getattribute__(self, name)
    else:
      return getattr(self.__ast__, name)

  def __setattr__(self, name, value):
    return object.__setattr__(self, name, value)

  def merge(self):
    ast = copy.copy(self.__ast__)
    __reserved_names__ = object.__getattribute__(self, '__reserved_names__')
    d = object.__getattribute__(self, '__dict__')
    for k, v in enumerate(d):
      if name in __reserved_names__:
        setattr(ast, name, d[name])
    return ast


class JSTransformer(ast.NodeVisitor):
  def generic_visit(self, node):
    if not isinstance(node, MagicPyAST):
      node = MagicPyAST(node)
    return super().generic_visit(MagicPyAST(node)).merge()

  def visit_Module(self, node):
    node = self.generic_visit(node)
    block = js_ast.BlockStatement(
      body=node.body)
    func = js_ast.FunctionExpression(
      params=[],
      body=block)
    call = js_ast.CallExpression(
      callee=func,
      arguments=[])
    expr = js_ast.ExpressionStatement(call)
    return js_ast.Program(body=expr)

  def visit_Import(self, node):
    print(ast.dump(node))

  def visit_ImportFrom(self, node):
    print(ast.dump(node))

  def visit_Expr(self, node):
    node = self.generic_visit(node)
    return js_ast.ExpressionStatement(node.value)

  def visit_BinOp(self, node):
    node = self.generic_visit(node)
    return js_ast.BinaryExpression(
      operator=node.op,
      left=node.left,
      right=node.right)

  def visit_Add(self, node):
    return js_ast.BinaryOperator('+')

  def visit_Num(self, node):
    return js_ast.Literal(node.n)

  def visit_Call(self, node):
    print(ast.dump(node))
