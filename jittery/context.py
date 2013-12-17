
import copy

import jittery.js.ast as js_ast

class NonlocalError(Exception): pass
class ContextNotFound(Exception):
  def __init__(self, name):
    super().__init__('%s not found in any context' % name)

class Context():
  def __init__(self, base_obj=None, nonlocals=None):
    if nonlocals is None:
      nonlocals = []
    self.base_obj = base_obj
    self.nonlocals = nonlocals
    self.vars = {}

  def to_js(self, name):
    if self.base_obj:
      return js_ast.MemberExpression(
        object=self.base_obj,
        property=js_ast.Literal(name),
        computed=True)
    else:
      return js_ast.Identifier(name)

  def __setitem__(self, name, codename=None):
    if name in self.nonlocals:
      raise NonlocalError()
    self.vars[name] = self.to_js(codename or name)

  def __getitem__(self, name):
    return self.vars[name]

  def __delitem__(self, name):
    if name in self.nonlocals:
      raise NonlocalError()
    del self.vars[name]

  def __contains__(self, name):
    return name in self.vars

class ContextStack():
  def __init__(self, global_ctx=None):
    if not global_ctx:
      global_ctx = Context()
    self.stack = []
    self.global_ctx = global_ctx
    self.stack.append(self.global_ctx)

  def find_context(self, name, mode='get'):
    assert mode in ('get', 'set', 'del')
    find_existing = mode in ('get', 'del')
    for ctx in reversed(self.stack):
      if not find_existing and name in ctx.nonlocals:
        find_existing = True
        break
      if not find_existing or name in ctx:
        return ctx
    raise ContextNotFound(name)

  def assign(self, name, val):
    ctx = self.find_context(name, mode='set')
    exists = name in ctx
    if exists:
      left = ctx[name]
    else:
      ctx[name] = None
      left = ctx[name]
    if exists or not isinstance(left, js_ast.Identifier):
      return js_ast.ExpressionStatement(
        js_ast.AssignmentExpression(
          operator=js_ast.AssignmentOperator('='),
          left=left,
          right=val))
    else:
      return js_ast.VariableDeclaration(
        declarations=[
          js_ast.VariableDeclarator(
            id=left,
            init=val)
        ])

  def __setitem__(self, name, val=None):
    ctx = self.find_context(name, mode='set')
    ctx[name] = val

  def __getitem__(self, name):
    ctx = self.find_context(name)
    return ctx[name]

  def __delitem__(self, name):
    ctx = self.find_context(name, mode='del')
    del ctx[name]

  def __contains__(self, name):
    try:
      ctx = self.find_context(name)
      return True
    except ContextNotFound:
      return False

  def __len__(self):
    return len(self.stack)

  def append(self, ctx=None):
    ctx = ctx or Context()
    self.stack.append(ctx)
    return ctx

  def pop(self):
    return self.stack.pop()

  def temporary(self, ctx=None):
    return TemporaryContext(self, ctx)

class TemporaryContext():
  def __init__(self, context, ctx=None):
    self.context = context
    self.arg = ctx

  def __enter__(self):
    if self.arg is not None:
      return self.context.append(self.arg)
    else:
      return self.context.append()

  def __exit__(self, exception_type, exception_value, traceback):
    self.context.pop()
