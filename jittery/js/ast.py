"""A way to generate javascript ASTs. Compatible with the Mozilla
javascript AST documented here:
https://developer.mozilla.org/en-US/docs/SpiderMonkey/Parser_API
"""

import inspect
import json
import types

class JSBase():
  def __iter__(self):
    yield self

class Node(JSBase):
  __properties__ = {
    'loc': {'default': None},
    'type': {'set_default': lambda self: self.__class__.__name__}
  }
  def __init__(self, **kwargs):
    props = self.get_properties()
    for prop, attrs in props.items():
      if 'default' in attrs:
        value = kwargs.get(prop, attrs['default'])
      elif 'set_default' in attrs:
        should_set = object()
        value = kwargs.get(prop, should_set)
        if value is should_set:
          value = attrs['set_default'](self)
      else:
        value = kwargs[prop]
      allowed = attrs.get('in', None)
      if allowed:
        assert value in allowed, (
          'Value %s for %s not allowed. '
          'Should be one of %s'
        ) % (valu, prop, allowed)
      setattr(self, prop, value)

  def get_properties(self):
    props = {}
    for cls in inspect.getmro(self.__class__):
      cls_props = getattr(cls, '__properties__', None)
      if cls_props:
        props.update(cls_props)
    return props

  def _typed_property(Class, prop_name, Type):
    _prop_name = '_%s' % prop_name

    def get_prop(self):
      return getattr(self, _prop_name)

    def set_prop(self, value):
      if value is not None and not isinstance(value, Type):
        value = Type(value)
      setattr(self, _prop_name, value)

    def del_prop(self):
      delattr(self, _prop_name)

    prop = property(get_prop, set_prop, del_prop)
    setattr(Class, prop_name, prop)

  def _properties(Class, props):
    Class.__properties__ = props

  def properties(**props):
    def wrapper(Class):
      for prop, attrs in props.items():
        Type = attrs.get('type', None)
        if Type:
          Node._typed_property(Class, prop, Type)
      Node._properties(Class, props)
      return Class
    return wrapper

class JSONEncoder(json.JSONEncoder):
  def default(self, node):
    if isinstance(node, Node):
      dict_ = {}
      for p, _ in node.get_properties().items():
        dict_[p] = getattr(node, p)
      return dict_
    elif isinstance(node, Operator):
      return node.operator
    else:
      return node.__dict__

class Statement(Node): pass
class Declaration(Statement): pass
class Pattern(Node): pass
class Expression(Pattern, Node): pass

class SourceLocation():
  def __init__(self, start, end, source=None):
    self.start = start
    self.end = end
    self.source = source

class Position():
  def __init__(self, line, column):
    self.line = line
    self.column = column
    assert self.line >= 1
    assert self.column >= 0

@Node.properties(body={})
class Program(Node): pass

@Node.properties(body={})
class BlockStatement(Statement):
  def __init__(self, body, **kwargs):
    kwargs['body'] = body
    super().__init__(**kwargs)

@Node.properties(
  params={},
  body={'type': BlockStatement},
  id={'default': None},
  defaults={'default': None},
  rest={'default': None},
  generator={'default': None})
class Function(Node): pass

class EmptyStatement(Statement): pass

@Node.properties(
  expression={})
class ExpressionStatement(Statement):
  def __init__(self, expression, **kwargs):
    kwargs['expression'] = expression
    super().__init__(**kwargs)

@Node.properties(
  test={},
  consequent={'type': BlockStatement},
  alternate={'type': BlockStatement, 'default': None})
class IfStatement(Statement): pass

@Node.properties(
  label={},
  body={})
class LabeledStatement(Statement): pass

@Node.properties(
  label={'default': None})
class BreakStatement(Statement): pass

@Node.properties(
  label={'default': None})
class ContinueStatement(Statement): pass

@Node.properties(
  object={},
  body={'type': BlockStatement})
class WithStatement(Statement): pass

@Node.properties(
  discriminant={},
  cases={},
  lexical={})
class SwitchStatement(Statement): pass

@Node.properties(
  argument={'default': None})
class ReturnStatement(Statement):
  def __init__(self, argument=None, **kwargs):
    kwargs['argument'] = argument
    super().__init__(**kwargs)

@Node.properties(
  argument={})
class ThrowStatement(Statement): pass

@Node.properties(
  block={'type': BlockStatement},
  handler={'default': None, 'type': BlockStatement},
  finalizer={'default': None, 'type': BlockStatement})
class TryStatement(Statement): pass

@Node.properties(
  test={},
  body={'type': BlockStatement})
class WhileStatement(Statement): pass

@Node.properties(
  body={'type': BlockStatement},
  test={})
class DoWhileStatement(Statement): pass

@Node.properties(
  body={'type': BlockStatement},
  init={'default': None},
  test={'default': None},
  update={'default': None})
class ForStatement(Statement): pass

@Node.properties(
  left={},
  right={},
  body={'type': BlockStatement},
  each={})
class ForInStatement(Statement): pass

@Node.properties(
  left={},
  right={},
  body={'type': BlockStatement})
class ForOfStatement(Statement): pass

@Node.properties(
  head={},
  body={'type': BlockStatement})
class LetStatement(Statement): pass

class LetHeadEntry():
  def __init__(self, id, init=None):
    self.id = id
    self.init = init

class DebuggerStatement(Statement): pass

@Node.properties(
  id={})
class FunctionDeclaration(Function, Declaration): pass

@Node.properties(
  declarations={},
  kind={'default': 'var', 'in': ('var', 'let', 'const')})
class VariableDeclaration(Declaration): pass

@Node.properties(
  id={},
  init={'default': None})
class VariableDeclarator(Node): pass

class ThisExpression(Expression): pass

@Node.properties(
  elements={'default': []})
class ArrayExpression(Expression): pass

@Node.properties(
  properties={'default': []})
class ObjectExpression(Expression): pass

class ObjectKey():
  def __init__(self, key, value, kind='init'):
    self.key = key
    self.value = value
    self.kind = kind

class FunctionExpression(Function, Expression): pass

@Node.properties(
  expressions={})
class SequenceExpression(Expression):
  def __init__(self, *expressions, **kwargs):
    kwargs['expressions'] = expressions
    super().__init__(**kwargs)

@Node.properties(
  operator={},
  argument={},
  prefix={'default': True})
class UnaryExpression(Expression): pass

@Node.properties(
  operator={},
  left={},
  right={})
class BinaryExpression(Expression): pass

@Node.properties(
  operator={'default': '='},
  left={},
  right={})
class AssignmentExpression(Expression): pass

@Node.properties(
  operator={},
  argument={},
  prefix={})
class UpdateExpression(Expression): pass

@Node.properties(
  operator={},
  left={},
  right={})
class LogicalExpression(Expression): pass

@Node.properties(
  test={},
  alternate={},
  consequent={})
class ConditionalExpression(Expression): pass

@Node.properties(
  callee={},
  arguments={})
class NewExpression(Expression): pass

@Node.properties(
  callee={},
  arguments={})
class CallExpression(Expression): pass

@Node.properties(
  object={},
  property={},
  computed={'default': False})
class MemberExpression(Expression): pass

@Node.properties(
  argument={'default': None})
class YieldExpression(Expression): pass

@Node.properties(
  head={},
  body={})
class LetExpression(Expression): pass

@Node.properties(
  properties={})
class ObjectPattern(Pattern): pass

@Node.properties(
  elements={})
class ArrayPattern(Pattern): pass

@Node.properties(
  consequent={},
  test={'default': None})
class SwitchCase(Node): pass

@Node.properties(
  param={},
  body={})
class CatchClause(Node): pass

@Node.properties(
  name={})
class Identifier(Expression, Pattern, Node):
  def __init__(self, name, **kwargs):
    kwargs['name'] = name
    super().__init__(**kwargs)

@Node.properties(
  value={})
class Literal(Expression, Node):
  def __init__(self, value, **kwargs):
    kwargs['value'] = value
    super().__init__(**kwargs)

class Operator(JSBase):
  valid_ops = set()

  def __init__(self, op):
    assert op in self.valid_ops, \
      '"%s" is not a valid %s' % (op, self.__class__.__name__)
    self.operator = op

class UnaryOperator(Operator):
  valid_ops = set(('-', '+', '!', '~', 'typeof', 'void', 'delete'))

class BinaryOperator(Operator):
  valid_ops = set(('==', '!=', '===', '!==' , '<', '<=', '>', '>=' ,
                   '<<', '>>', '>>>' , '+', '-', '*', '/', '%' , '|',
                   '^', '&', 'in', 'instanceof'))

class LogicalOperator(Operator):
  valid_ops = set(('||', '&&'))

class AssignmentOperator(Operator):
  valid_ops = set(('=', '+=', '-=', '*=', '/=', '%=' , '<<=',
                   '>>=', '>>>=', '|=', '^=', '&='))

class UpdateOperator(Operator):
  valid_ops = set(('--', '++'))
