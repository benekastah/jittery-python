import ast


def name(name, ctx=None):
    return ast.Name(name, ctx or ast.Load())


def assign(target, value):
    try:
        it = iter(target)
    except TypeError:
        it = [target]

    def fix_target(target):
        if isinstance(target, ast.Name) and not isinstance(target.ctx, ast.Store):
            return ast.copy_location(name(target.id, ast.Store()), target)
        return target

    it = [fix_target(t) for t in it]
    return ast.Assign(it, value)


def new_scope(body, ret):
    body = list(body)
    body.append(ast.Return(ret))
    fn = ast.FunctionDef(
        None,
        ast.arguments([], None, [], None, [], []),
        body, [], None)
    return ast.Call(fn, [], [])


def to_ast(val):
    if isinstance(val, ast.AST):
        return val
    elif isinstance(val, ASTBuilder):
        return val.node
    elif val is True:
        return ast.NameConstant('True')
    elif val is False:
        return ast.NameConstant('False')
    elif val is None:
        return ast.NameConstant('None')
    elif isinstance(val, (float, int)):
        return ast.Num(val)
    elif isinstance(val, str):
        return ast.Str(val)
    else:
        return NotImplementedError(val)


class ASTBuilder:

    def __init__(self, node):
        self.node = to_ast(node)

    def __call__(self, *args, **kwargs):
        return ASTBuilder(ast.Call(
            self.node,
            [to_ast(n) for n in args],
            [ast.keyword(k, to_ast(n)) for k, n in kwargs.items()]))

    def __gt__(self, other):
        return ASTBuilder(ast.Compare(
            self.node,
            [ast.Gt()],
            to_ast(other)))

    def __lt__(self, other):
        return ASTBuilder(ast.Compare(
            self.node,
            [ast.Lt()],
            to_ast(other)))

    def __ge__(self, other):
        return ASTBuilder(ast.Compare(
            self.node,
            [ast.GtE()],
            to_ast(other)))

    def __le__(self, other):
        return ASTBuilder(ast.Compare(
            self.node,
            [ast.LtE()],
            to_ast(other)))

    def __add__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node,
            ast.Add(),
            to_ast(other)))

    def __sub__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node,
            ast.Sub(),
            to_ast(other)))

    def __mul__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node,
            ast.Mult(),
            to_ast(other)))

    def __truediv__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node, ast.Div(), to_ast(other)))

    def __floordiv__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node, ast.FloorDiv(), to_ast(other)))

    def __mod__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node, ast.Mod(), to_ast(other)))

    def __pow__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node, ast.Pow(), to_ast(other)))

    def __lshift__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node, ast.LShift(), to_ast(other)))

    def __rshift__(self, other):
        return ASTBuilder(ast.BinOp(
            self.node, ast.RShift(), to_ast(other)))

    def __getattr__(self, attr):
        return self.attr(attr)

    def __getitem__(self, key):
        return ASTBuilder(ast.Subscript(self.node, ast.Index(to_ast(key)), ast.Load()))


    def attr(self, attr):
        return ASTBuilder(ast.Attribute(self.node, attr, ast.Load()))
