"""A way to generate javascript ASTs. Compatible with the Mozilla
javascript AST documented here:
https://developer.mozilla.org/en-US/docs/SpiderMonkey/Parser_API
"""

import json

class Node():
  def __init__(self, loc=None):
    self.type = self.__class__.__name__
    self.loc = loc

class NodeJSONEncoder(json.JSONEncoder):
  def default(self, node):
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

class Program(Node):
  def __init__(self, body, **kwargs):
    self.body = body
    super().__init__(**kwargs)

class Function(Node):
  def __init__(self, params, body, id=None, defaults=None, rest=None, generator=False, **kwargs):
    self.id = id
    self.params = params
    self.defaults = defaults
    self.rest = rest
    self.body = body
    self.generator = generator
    self.expression = isinstance(body, Expression)
    super().__init__(**kwargs)

class EmptyStatement(Statement): pass

class BlockStatement(Statement):
  def __init__(self, body, **kwargs):
    self.body = body
    super().__init__(**kwargs)

class ExpressionStatement(Statement):
  def __init__(self, expression, **kwargs):
    self.expression = expression
    super().__init__(**kwargs)

class IfStatement(Statement):
  def __init__(self, test, consequent, alternate=None, **kwargs):
    self.test = test
    self.consequent = consequent
    self.alternate = alternate
    super().__init__(**kwargs)

class LabeledStatement(Statement):
  def __init__(self, label, body, **kwargs):
    self.label = label
    self.body = body
    super().__init__(**kwargs)

class BreakStatement(Statement):
  def __init__(self, label=None, **kwargs):
    self.label = label
    super().__init__(**kwargs)

class ContinueStatement(Statement):
  def __init__(self, label=None, **kwargs):
    self.label = label
    super().__init__(**kwargs)

class WithStatement(Statement):
  def __init__(self, object, body, **kwargs):
    self.object = object
    self.body = body
    super().__init__(**kwargs)

class SwitchStatement(Statement):
  def __init__(self, discriminant, cases, lexical, **kwargs):
    self.discriminant = discriminant
    self.cases = cases
    self.lexical = lexical
    super().__init__(**kwargs)

class ReturnStatement(Statement):
  def __init__(self, argument=None, **kwargs):
    self.argument = argument
    super().__init__(**kwargs)

class ThrowStatement(Statement):
  def __init__(self, argument, **kwargs):
    self.argument = argument
    super().__init__(**kwargs)

class TryStatement(Statement):
  def __init__(self, block, handler=None, finalizer=None, **kwargs):
    self.block = block
    self.handler = handler
    self.finalizer = finalizer
    super().__init__(**kwargs)

class WhileStatement(Statement):
  def __init__(self, test, body, **kwargs):
    self.test = test
    self.body = body
    super().__init__(**kwargs)

class DoWhileStatement(Statement):
  def __init__(self, body, test, **kwargs):
    self.body = body
    self.test = test
    super().__init__(**kwargs)

class ForStatement(Statement):
  def __init__(self, body, init=None, test=None, update=None, **kwargs):
    self.body = body
    self.init = init
    self.test = test
    self.update = update
    super().__init__(**kwargs)

class ForInStatement(Statement):
  def __init__(self, left, right, body, each, **kwargs):
    self.left = left
    self.right = right
    self.body = body
    self.each = each
    super().__init__(**kwargs)

class ForOfStatement(Statement):
  def __init__(self, left, right, body, **kwargs):
    self.left = left
    self.right = right
    self.body = body
    super().__init__(**kwargs)

class LetStatement(Statement):
  def __init__(self, head, body, **kwargs):
    self.head = head
    self.body = body
    super().__init__(**kwargs)

class LetHeadEntry():
  def __init__(self, id, init=None):
    self.id = id
    self.init = init

class DebuggerStatement(Statement): pass

class FunctionDeclaration(Function, Declaration):
  def __init__(self, id, **kwargs):
    kwargs['id'] = id
    super().__init__(**kwargs)

class VariableDeclaration(Declaration):
  def __init__(self, declarations, kind='var', **kwargs):
    self.declarations = declarations
    self.kind = kind
    assert self.kind in ('var', 'let', 'const')
    super().__init__(**kwargs)

class VariableDeclarator(Node):
  def __init__(self, id, init=None, **kwargs):
    self.id = id
    self.init = init
    super().__init__(**kwargs)

class ThisExpression(Expression): pass

class ArrayExpression(Expression):
  def __init__(self, elements, **kwargs):
    self.elements = elements
    super().__init__(**kwargs)

class ObjectExpression(Expression):
  def __init__(self, properties, **kwargs):
    self.properties = properties
    super().__init__(**kwargs)

class ObjectKey():
  def __init__(self, key, value, kind='init'):
    self.key = key
    self.value = value
    self.kind = kind

class FunctionExpression(Function, Expression): pass

class ArrowExpression(Function, Expression):
  def __init__(self, **kwargs):
    assert 'id' not in kwargs
    super().__init__(**kwargs)

class SequenceExpression(Expression):
  def __init__(self, expressions, **kwargs):
    self.expressions = expressions
    super().__init__(**kwargs)

class UnaryExpression(Expression):
  def __init__(self, operator, prefix, argument, **kwargs):
    self.operator = operator
    self.prefix = prefix
    self.argument = argument
    super().__init__(**kwargs)

class BinaryExpression(Expression):
  def __init__(self, operator, left, right, **kwargs):
    self.operator = operator
    self.left = left
    self.right = right
    super().__init__(**kwargs)

class AssignmentExpression(Expression):
  def __init__(self, operator, left, right, **kwargs):
    self.operator = operator
    self.left = left
    self.right = right
    super().__init__(**kwargs)

class UpdateExpression(Expression):
  def __init__(self, operator, argument, prefix, **kwargs):
    self.operator = operator
    self.argument = argument
    self.prefix = prefix
    super().__init__(**kwargs)

class LogicalExpression(Expression):
  def __init__(self, operator, left, right, **kwargs):
    self.operator = operator
    self.left = left
    self.right = right
    super().__init__(**kwargs)

class ConditionalExpression(Expression):
  def __init__(self, test, alternate, consequent, **kwargs):
    self.test = test
    self.alternate = alternate
    self.consequent = consequent
    super().__init__(**kwargs)

class NewExpression(Expression):
  def __init__(self, callee, arguments, **kwargs):
    self.callee = callee
    self.arguments = arguments
    super().__init__(**kwargs)

class CallExpression(Expression):
  def __init__(self, callee, arguments, **kwargs):
    self.callee = callee
    self.arguments = arguments
    super().__init__(**kwargs)

class MemberExpression(Expression):
  def __init__(self, object, property, **kwargs):
    self.object = object
    self.property = property
    self.computed = isinstance(self.property, Expression)
    super().__init__(**kwargs)

class YieldExpression(Expression):
  def __init__(self, argument=None, **kwargs):
    self.argument = argument
    super().__init__(**kwargs)

class LetExpression(Expression):
  def __init__(self, head, body, **kwargs):
    self.head = head
    self.body = body
    super().__init__(**kwargs)

class ObjectPattern(Pattern):
  def __init__(self, properties, **kwargs):
    self.properties = properties
    super().__init__(**kwargs)

class ArrayPattern(Pattern):
  def __init__(self, elements, **kwargs):
    self.elements = elements
    super().__init__(**kwargs)

class SwitchCase(Node):
  def __init__(self, consequent, test=None, **kwargs):
    self.consequent = consequent
    self.test = test
    super().__init__(**kwargs)

class CatchClause(Node):
  def __init__(self, param, body, **kwargs):
    self.param = param
    self.body = body
    super().__init__(**kwargs)

class Identifier(Expression, Pattern, Node):
  def __init__(self, name, **kwargs):
    self.name = name
    super().__init__(**kwargs)

class Literal(Expression, Node):
  def __init__(self, value, **kwargs):
    self.value = value
    super().__init__(**kwargs)

def operators(*ops):
  _ops = set(ops)
  def wrapped(op):
    assert op in _ops, '"%s" not in %s' % (op, _ops)
    return op
  return wrapped

UnaryOperator = operators('-', '+', '!', '~', 'typeof', 'void', 'delete')

BinaryOperator = operators('==', '!=', '===', '!==' , '<', '<=', '>', '>=' ,
                           '<<', '>>', '>>>' , '+', '-', '*', '/', '%' , '|',
                           '^', '&', 'in', 'instanceof')

LogicalOperator = operators('||', '&&')

AssignmentOperator = operators('=', '+=', '-=', '*=', '/=', '%=' , '<<=',
                               '>>=', '>>>=', '|=', '^=', '&=')

UpdateOperator = operators('--', '++')
