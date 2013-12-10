
import ast
import copy

import jittery.js.ast as js_ast

class JSTransformer(ast.NodeTransformer):
  def visit_Module(self, node):
    self.generic_visit(node)
    block = js_ast.BlockStatement(
      body=node.body)
    func = js_ast.FunctionExpression(
      params=[],
      body=block)
    call = js_ast.CallExpression(
      callee=func,
      arguments=[])
    expr = js_ast.ExpressionStatement(call)
    return js_ast.Program(body=[expr])

  def visit_Import(self, node):
    print(ast.dump(node))

  def visit_ImportFrom(self, node):
    print(ast.dump(node))

  def visit_Expr(self, node):
    self.generic_visit(node)
    return js_ast.ExpressionStatement(node.value)

  def visit_BinOp(self, node):
    self.generic_visit(node)
    return js_ast.BinaryExpression(
      operator=node.op,
      left=node.left,
      right=node.right)

  def visit_Add(self, node):
    return js_ast.BinaryOperator('+')

  def visit_Mult(self, node):
    return js_ast.BinaryOperator('*')

  def visit_Num(self, node):
    return js_ast.Literal(node.n)

  def visit_Call(self, node):
    self.generic_visit(node)
    assert not node.keywords, 'Keyword arguments not supported'
    assert not node.starargs, 'Starargs/rest arguments not supported'
    assert not node.kwargs, 'Keyword arguments not supported'
    return js_ast.CallExpression(node.func, node.args)

  def visit_Name(self, node):
    return js_ast.Identifier(node.id)

  def visit_Attribute(self, node):
    self.generic_visit(node)
    return js_ast.MemberExpression(
      node.value,
      js_ast.Identifier(node.attr))

  def visit_FunctionDef(self, node):
    # print(ast.dump(node))
    self.generic_visit(node)
    assert not node.args.vararg, 'Vararg/rest arguments not supported'
    assert not node.args.kwonlyargs, 'Keyword arguments not supported'
    assert not node.args.kwarg, 'Keyword arguments not supported'
    assert not node.args.defaults, 'Default arguments not supported'
    assert not node.args.kw_defaults, 'Default arguments not supported'
    assert not node.decorator_list, 'Decorators not supported'

    params = [js_ast.Identifier(arg.arg) for arg in node.args.args]
    return js_ast.FunctionDeclaration(
      id=js_ast.Identifier(node.name),
      params=params,
      body=js_ast.BlockStatement(node.body))

  def visit_Return(self, node):
    self.generic_visit(node)
    return js_ast.ReturnStatement(node.value)

