
import ast
import copy

import jittery.js.ast as js_ast

class NotImplementedError(Exception):
  def __init__(self, node):
    self.node = node
    msg = ast.dump(self.node)
    super().__init__(msg)

class BinaryOperatorWrapper():
  def __init__(self, wrap):
    self.wrap = wrap

def _makeBinaryExpression(op, left, right):
  if isinstance(op, BinaryOperatorWrapper):
    return op.wrap(left, right)
  else:
    return js_ast.BinaryExpression(
      operator=op,
      left=left,
      right=right)

class JSTransformer(ast.NodeTransformer):
  def __init__(self, context, bare=False, **kwargs):
    self.context = context
    self.bare = bare
    super().__init__(**kwargs)

  def visit_Module(self, node):
    with self.context.temporary() as file_ctx, \
         self.context.temporary() as module_ctx:
      file_ctx['__module__'] = None
      module_id = js_ast.Identifier('__module__')
      module_obj = js_ast.ObjectExpression(
        properties=[])
      module_ctx.base_obj = module_id
      name = self.context.assign('__name__', js_ast.Literal('__main__'))
      self.generic_visit(node)
      if self.bare:
        return js_ast.Program(body=node.body)
      else:
        body = [
          name
        ] + node.body + [
          js_ast.ReturnStatement(module_id)
        ]
        func = js_ast.FunctionExpression(
          params=[module_id],
          body=body)
        call = js_ast.CallExpression(
          callee=func,
          arguments=[module_obj])
        expr = js_ast.ExpressionStatement(call)
        return js_ast.Program(body=[expr])

  def visit_Expr(self, node):
    self.generic_visit(node)
    return js_ast.ExpressionStatement(node.value)

  def visit_BinOp(self, node):
    self.generic_visit(node)
    return _makeBinaryExpression(node.op, node.left, node.right)

  def visit_Add(self, node):
    return js_ast.BinaryOperator('+')

  def visit_Mult(self, node):
    return js_ast.BinaryOperator('*')

  def visit_Sub(self, node):
    return js_ast.BinaryOperator('-')

  def visit_Div(self, node):
    return js_ast.BinaryOperator('/')

  def visit_FloorDiv(self, node):
    def wrapper(left, right):
      math_floor = js_ast.MemberExpression(
        object=js_ast.Identifier('Math'),
        property=js_ast.Identifier('floor'))
      bin_op = js_ast.BinaryExpression(
        operator=js_ast.BinaryOperator('/'),
        left=left,
        right=right)
      return js_ast.CallExpression(
        callee=math_floor,
        arguments=[bin_op])
    return BinaryOperatorWrapper(wrapper)

  def visit_Pow(self, node):
    def wrapper(left, right):
      math_pow = js_ast.MemberExpression(
        object=js_ast.Identifier('Math'),
        property=js_ast.Identifier('pow'))
      return js_ast.CallExpression(
        callee=math_pow,
        arguments=[left, right])
    return BinaryOperatorWrapper(wrapper)

  def visit_Num(self, node):
    return js_ast.Literal(node.n)

  def visit_Call(self, node):
    self.generic_visit(node)
    assert not node.keywords, 'Keyword arguments not supported'
    assert not node.starargs, 'Starargs/rest arguments not supported'
    assert not node.kwargs, 'Keyword arguments not supported'
    return js_ast.CallExpression(node.func, node.args)

  def visit_Name(self, node):
    name = node.id
    if name in self.context:
      return self.context[name]
    else:
      return js_ast.Identifier(name)

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

    ident = js_ast.Identifier(node.name)
    params = [js_ast.Identifier(arg.arg) for arg in node.args.args]
    func = js_ast.FunctionExpression(
      id=ident,
      params=params,
      body=js_ast.BlockStatement(node.body))
    return self.context.assign(node.name, func)

  def visit_Return(self, node):
    self.generic_visit(node)
    return js_ast.ReturnStatement(node.value)

  def visit_Expression(self, node):
    raise NotImplementedError(node)

  def visit_Try(self, node):
    raise NotImplementedError(node)

  def visit_IsNot(self, node):
    return js_ast.BinaryOperator('!==')

  def visit_BoolOp(self, node):
    raise NotImplementedError(node)

  # def visit_Del(self, node):
  #   raise NotImplementedError(node)

  def visit_UAdd(self, node):
    return js_ast.UnaryOperator('+')

  def visit_Not(self, node):
    return js_ast.UnaryOperator('!')

  def visit_ExtSlice(self, node):
    raise NotImplementedError(node)

  def visit_Mod(self, node):
    return js_ast.BinaryOperator('%')
    raise NotImplementedError(node)

  def visit_Delete(self, node):
    return js_ast.UnaryOperator('delete')

  def visit_Slice(self, node):
    raise NotImplementedError(node)

  def visit_Raise(self, node):
    raise NotImplementedError(node)

  def visit_USub(self, node):
    return js_ast.UnaryOperator('-')

  def visit_With(self, node):
    raise NotImplementedError(node)

  def visit_SetComp(self, node):
    raise NotImplementedError(node)

  def visit_LShift(self, node):
    return js_ast.BinaryOperator('<<')

  def visit_If(self, node):
    self.generic_visit(node)
    return js_ast.IfStatement(
      test=node.test,
      consequent=js_ast.BlockStatement(node.body),
      alternate=js_ast.BlockStatement(node.orelse))

  def visit_Break(self, node):
    return js_ast.BreakStatement()

  def visit_LtE(self, node):
    raise NotImplementedError(node)

  def visit_ClassDef(self, node):
    raise NotImplementedError(node)

  def visit_NotIn(self, node):
    raise NotImplementedError(node)

  def visit_Is(self, node):
    return js_ast.BinaryOperator('===')

  def visit_Interactive(self, node):
    raise NotImplementedError(node)

  def visit_Store(self, node):
    raise NotImplementedError(node)

  def visit_Set(self, node):
    raise NotImplementedError(node)

  def visit_Param(self, node):
    raise NotImplementedError(node)

  def visit_In(self, node):
    raise NotImplementedError(node)

  def visit_Eq(self, node):
    raise NotImplementedError(node)

  # def visit_Index(self, node):
  #   raise NotImplementedError(node)

  # def visit_Load(self, node):
  #   raise NotImplementedError(node)

  def visit_Lambda(self, node):
    raise NotImplementedError(node)

  def visit_RShift(self, node):
    return js_ast.BinaryOperator('>>')

  def visit_Compare(self, node):
    self.generic_visit(node)
    left = node.left

    def make_blank():
      return js_ast.LogicalExpression(
        operator=js_ast.LogicalOperator('&&'),
        left=None,
        right=None)

    result = make_blank()
    this_result = result

    def add_compare(compare):
      nonlocal this_result
      if not this_result.left:
        this_result.left = compare
      elif not this_result.right:
        this_result.right = compare
      else:
        blank = make_blank()
        blank.left = this_result.right
        blank.right = compare
        this_result.right = blank
        this_result = blank

    for op, right in zip(node.ops, node.comparators):
      add_compare(_makeBinaryExpression(op, left, right))
      left = right

    return result if result.right else result.left

  def visit_IfExp(self, node):
    raise NotImplementedError(node)

  def visit_Pass(self, node):
    return js_ast.EmptyStatement()

  def visit_Yield(self, node):
    raise NotImplementedError(node)

  def visit_GtE(self, node):
    raise NotImplementedError(node)

  def visit_YieldFrom(self, node):
    raise NotImplementedError(node)

  def visit_Gt(self, node):
    raise NotImplementedError(node)

  def visit_AugStore(self, node):
    raise NotImplementedError(node)

  def visit_List(self, node):
    self.generic_visit(node)
    return js_ast.ArrayExpression(
      elements=node.elts)

  def visit_BitOr(self, node):
    return js_ast.BinaryOperator('|')

  def visit_Tuple(self, node):
    raise NotImplementedError(node)

  def visit_ListComp(self, node):
    raise NotImplementedError(node)

  def visit_PyCF_ONLY_AST(self, node):
    raise NotImplementedError(node)

  def visit_NotEq(self, node):
    raise NotImplementedError(node)

  def visit_UnaryOp(self, node):
    self.generic_visit(node)
    return js_ast.UnaryExpression(
      operator=node.op,
      argument=node.operand)

  def visit_For(self, node):
    raise NotImplementedError(node)

  def visit_Bytes(self, node):
    raise NotImplementedError(node)

  def visit_BitAnd(self, node):
    return js_ast.BinaryOperator('&')

  def visit_Assign(self, node):
    self.generic_visit(node)
    if len(node.targets) is 1:
      return self.context.assign(node.targets[0].name, node.value)
    else:
      expressions = []
      for i, target in enumerate(node.targets):
        expressions.append(
          self.context.assign(target.name, js_ast.MemberExpression(
            object=node.value,
            property=i,
            computed=True)))
      return js_ast.SequenceExpression(expressions)

  def visit_And(self, node):
    return js_ast.LogicalOperator('&&')

  def visit_ImportFrom(self, node):
    raise NotImplementedError(node)

  def visit_AugLoad(self, node):
    raise NotImplementedError(node)

  def visit_Continue(self, node):
    return js_ast.ContinueStatement()

  def visit_Assert(self, node):
    raise NotImplementedError(node)

  def visit_Import(self, node):
    raise NotImplementedError(node)

  def visit_Dict(self, node):
    raise NotImplementedError(node)

  def visit_Ellipsis(self, node):
    raise NotImplementedError(node)

  def visit_Starred(self, node):
    raise NotImplementedError(node)

  def visit_Invert(self, node):
    return js_ast.UnaryOperator('~')

  def visit_AugAssign(self, node):
    raise NotImplementedError(node)

  def visit_DictComp(self, node):
    raise NotImplementedError(node)

  def visit_BitXor(self, node):
    return js_ast.BinaryOperator('^')

  def visit_Suite(self, node):
    raise NotImplementedError(node)

  def visit_ExceptHandler(self, node):
    raise NotImplementedError(node)

  def visit_While(self, node):
    raise NotImplementedError(node)

  def visit_GeneratorExp(self, node):
    raise NotImplementedError(node)

  def visit_Nonlocal(self, node):
    raise NotImplementedError(node)

  def visit_Str(self, node):
    return js_ast.Literal(node.s)

  def visit_Lt(self, node):
    return js_ast.BinaryOperator('<')

  def visit_Subscript(self, node):
    self.generic_visit(node)
    return js_ast.MemberExpression(
      object=node.value,
      property=node.slice.value,
      computed=True)

  def visit_Global(self, node):
    raise NotImplementedError(node)

  def visit_Or(self, node):
    return js_ast.BinaryOperator('||')


