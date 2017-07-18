from contextlib import contextmanager
import ast
import enum
import io
import random

from .builder import name, assign, new_scope
from .builder import ASTBuilder as _


def extend(ls, nodes):
    try:
        it = iter(nodes)
    except TypeError:
        it = [nodes]
    return ls.extend(list(it))


class Context:

    def __init__(self, parent=None, class_name=None):
        self.parent = parent
        self.vars = set()
        self.class_name = class_name

    def has_var(self, var):
        return var in self.vars

    def add_var(self, var):
        self.vars.add(var)

    def gensym(self, name=''):
        sym = '__{}{}'.format(name, random.randrange(1e5))
        self.add_var(sym)
        return sym

    def __iter__(self):
        yield from self.vars

    def __len__(self):
        return len(self.vars)

    def __bool__(self):
        return bool(self.vars)


class JavaScript:

    def __init__(self, fname, file):
        self.fname = fname
        self.file = file
        self._indent_level = 0

    @contextmanager
    def indented(self, indent_by=4):
        self._indent_level += indent_by
        yield
        self._indent_level -= indent_by

    @contextmanager
    def block(self, start=' {', end='}'):
        self.write(start)
        self.write('\n')
        with self.indented():
            yield
        self.indent()
        self.write('}')

    @contextmanager
    def line(self, eol=''):
        self.indent()
        yield
        self.write(eol)
        self.write('\n')

    def indent(self):
        self.write(''.join([' '] * self._indent_level))

    def write(self, *args, **kwargs):
        return self.file.write(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.file.seek(*args, **kwargs)

    def read(self, *args, **kwargs):
        return self.file.read(*args, **kwargs)


class Simplify(ast.NodeTransformer):

    def __init__(self):
        super().__init__()
        self.context = None

    @contextmanager
    def _block(self, class_name=None):
        self.context = Context(self.context, class_name)
        yield
        self.context = self.context.parent

    def _gensym(self, base=''):
        return name(self.context.gensym(base))

    def _name(self, n):
        self.context.add_var(n.id)
        return name(n)

    def _decorate(self, node, decorator_list):
        for decorator in decorator_list:
            node = ast.copy_location(_(decorator)(node).node, node)
        return node

    def visit_Module(self, node):
        with self._block():
            node = self.generic_visit(node)
            if self.context:
                var_assignment = ast.copy_location(
                    assign([name(var) for var in self.context], None), node)
                return ast.copy_location(
                    ast.Module([
                        var_assignment,
                        *node.body
                    ]), node)
            else:
                return node

    def visit_FunctionDef(self, node):
        assert not node.args.kwonlyargs
        assert not node.args.kw_defaults

        with self._block():
            node = self.generic_visit(node)
            body = []

            if node.args.defaults:
                for (n, arg), default in zip(
                        reversed(list(enumerate(node.args.args))), reversed(node.args.defaults)):
                    body.append(self.visit(ast.copy_location(
                        ast.If(
                            ast.Compare(_(name('arguments')).length.node, [ast.LtE()], [ast.Num(n)]),
                            [assign(name(arg.arg), default)],
                            []),
                        arg)))

            if node.args.vararg:
                body.append(self.visit(ast.copy_location(
                    assign(
                        name(node.args.vararg.arg),
                        _(name('Array')).prototype.slice.call(name('arguments'), len(node.args.args)).node),
                    node.args.vararg)))

            if node.args.kwarg:
                __js__ = _(name('__js__'))
                arguments = name(node.args.vararg.arg if node.args.vararg else 'arguments')
                peek_kwarg = _(name('arguments'))[_(name('arguments')).length - 1].node
                get_kwarg = None
                if node.args.vararg:
                    get_kwarg = _(name(node.args.vararg.arg)).pop().node
                else:
                    get_kwarg = peek_kwarg
                get_kwarg = ast.Expr(get_kwarg)
                body.append(self.visit(ast.copy_location(
                    ast.If(_(name('__is_kwarg__'))(peek_kwarg).node, [get_kwarg], []),
                    node.args.kwarg)))

            # Do this after processing other args
            context_args = self.context.vars - set(a.arg for a in node.args.args)
            if context_args:
                body.insert(0, ast.copy_location(
                    assign([name(var) for var in context_args], None),
                    node))
            body.extend(node.body)

        fn = ast.copy_location(
            ast.FunctionDef(node.name, node.args, body, [], node.returns),
            node)

        if node.name and (node.decorator_list or self.context.class_name):
            nodes = [fn]
            fn = self._decorate(name(node.name), node.decorator_list)
            extend(nodes, ast.copy_location(
                self.visit(assign(name(node.name), fn)),
                node))
            return nodes
        else:
            return self._decorate(fn, node.decorator_list)

    def visit_ClassDef(self, node):
        assert len(node.bases) <= 1
        assert not node.keywords

        nodes = []

        # Keep a reference to the original class so that reassigning to
        # node.name doesn't affect our ability to instantiate
        saved_cls = name(Context().gensym(node.name))
        nodes.append(ast.copy_location(
            assign(saved_cls, None),
            node))
        nodes.append(ast.copy_location(
            assign(saved_cls, name(node.name)),
            node))

        __js__ = _(name('__js__'))
        newcall = __js__('new (Function.prototype.bind.apply(' + saved_cls.id + ', arguments))')
        extend(nodes, self.visit(ast.copy_location(
            ast.FunctionDef(
                node.name,
                ast.arguments([], None, [], None, [], []), [
                    ast.If(__js__('!(this instanceof ' + saved_cls.id + ')').node, [ast.Return(newcall.node)], []),
                    ast.Expr(__js__('this.__init__ && this.__init__.apply(this, arguments)').node)
                ],
                node.decorator_list,
                None), node)))

        if node.bases:
            nodes.append(ast.copy_location(
                assign(
                    _(saved_cls).prototype.node,
                    _(name('Object')).create(_(node.bases[0]).prototype).node),
                node))

        with self._block(saved_cls.id):
            for entry in node.body:
                extend(nodes, self.visit(entry))

        return ast.copy_location(ast.Expr(new_scope(nodes, name(node.name))), node)

    def visit_Lambda(self, node):
        ret = ast.copy_location(
            ast.Return(node.body),
            node.body)
        return self.visit(ast.copy_location(
            ast.FunctionDef(None, node.args, [ret], [], None),
            node))

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.FloorDiv):
            return ast.copy_location(
                _(name('Math')).floor(_(node.left) / node.right).node,
                node)
        elif isinstance(node.op, ast.Pow):
            return ast.copy_location(
                _(name('Math')).pow(node.left, node.right).node,
                node)
        elif isinstance(node.op, ast.MatMult):
            raise NotImplementedError(node.op)
        else:
            return self.generic_visit(node)

    def visit_For(self, node):
        nodes = []
        it = self._gensym('iter')
        running = self._gensym('running')
        extend(nodes, ast.copy_location(
            assign(it, _(name('iter'))(node.iter).node),
            node))
        extend(nodes, ast.copy_location(
            assign(running, _(True).node),
            node))
        body = ast.copy_location(ast.Try([
            ast.copy_location(
                assign(node.target, _(name('next'))(it).node),
                node),
            *node.body
        ], [ast.ExceptHandler(name('StopIteration'), None, [
            assign(running, _(False).node)
        ])], [], []), node)
        while_nodes = self.visit(ast.copy_location(
            ast.While(running, [body], node.orelse),
            node))
        extend(nodes, while_nodes)
        return [self.generic_visit(n) for n in nodes]

    def visit_While(self, node):
        nodes = []

        br = None
        body = []
        for entry in node.body:
            if node.orelse and isinstance(entry, ast.Break):
                br = self._gensym('break')
                body.append(ast.copy_location(
                    assign(br, _(True).node),
                    entry))
            body.append(entry)

        nodes.append(ast.copy_location(
            ast.While(node.test, body, []),
            node))

        if br:
            nodes.append(ast.copy_location(
                ast.If(ast.UnaryOp(ast.Not(), br), node.orelse, []),
                node.orelse[0]))

        return [self.generic_visit(n) for n in nodes]

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.context.add_var(node.id)
            if self.context.class_name:
                return ast.copy_location(
                    _(name(self.context.class_name)).prototype.attr(node.id).node,
                    node)
        return node

    def visit_Compare(self, node):
        if len(node.ops) == 1:
            return node

        last = self._gensym('last')

        def store_compare(node):
            return ast.copy_location(
                assign(last, node),
                node)

        comparisons = []
        for i, (op, comp) in enumerate(zip(node.ops, node.comparators)):
            left = node.left if i == 0 else last
            if i < len(node.ops) - 1:
                comp = store_compare(comp)
            comparisons.append(ast.copy_location(
                ast.Compare(left, [op], [comp]),
                node))

        return self.generic_visit(ast.copy_location(
            ast.BoolOp(ast.And(), comparisons),
            node))

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if node.keywords:
            kwargs = self.visit(ast.copy_location(
                _(name('__make_kwarg__'))(
                    ast.Dict([ast.Str(k.arg) for k in node.keywords],
                             [k.value for k in node.keywords])).node,
                node))
            args = list(node.args)
            args.append(kwargs)
            node = ast.copy_location(
                ast.Call(node.func, args, []),
                node)

        grouped_args = []
        last_group = []
        has_starred = False
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                has_starred = True
                if last_group:
                    grouped_args.append(last_group)
                    grouped_args.append(arg)
                    last_group = []
            else:
                last_group.append(arg)
        if last_group:
            grouped_args.append(last_group)

        if has_starred:
            args = None
            for group in grouped_args:
                if isinstance(group, ast.Starred):
                    arg = group.value
                else:
                    arg = ast.List(group, ast.Load())
                if not args:
                    args = arg
                else:
                    args = _(args).concat(arg).node
            node = ast.copy_location(
                ast.Call(_(node.func).apply.node, [_(None).node, args], node.keywords),
                node)

        return node

    def visit_Dict(self, node):
        node = self.generic_visit(node)
        expand = []
        expr_kvs = []
        keys = []
        values = []
        for k, v in zip(node.keys, node.values):
            if k is None:
                expand.append(v)
            elif not isinstance(k, (ast.Str, ast.Num)):
                expr_kvs.append((k, v))
            else:
                keys.append(k)
                values.append(v)

        node = ast.copy_location(ast.Dict(keys, values), node)

        if expand:
            node = self.visit(ast.copy_location(
                _('Object').assign(node, *expand),
                node))

        if expr_kvs:
            d = self._gensym('d')
            body = [assign(d, node)]
            for k, v in expr_kvs:
                body.append(ast.copy_location(
                    assign(_(d)[k].node, v), k))
            body.append(ast.copy_location(ast.Return(d), node))
            node = self.visit(ast.copy_location(new_scope(body, d), node))

        return node


class ToJS(ast.NodeVisitor):

    def __init__(self, js, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_expr = [False]
        self.js = js

    def visit(self, node):
        self.in_expr.append(
            isinstance(node, ast.expr) or (
                isinstance(node, ast.FunctionDef) and
                not node.name))
        super().visit(node)
        self.in_expr.pop()

    def visit_children(self, node):
        return super().generic_visit(node)

    def generic_visit(self, node):
        raise NotImplementedError(node)

    @contextmanager
    def write_stmt(self):
        if self.in_expr[-1]:
            self.js.write('(')
            yield
            self.js.write(')')
        else:
            with self.js.line(';'):
                yield

    def visit_Module(self, node):
        self.js.indent()
        self.js.write('(function ()')
        with self.js.block():
            with self.write_stmt():
                self.js.write('"use strict"')
            self.visit_children(node)
        self.js.write(')();')

    def visit_Expr(self, node):
        with self.write_stmt():
            self.visit_children(node)

    def visit_Assign(self, node):
        with self.write_stmt():
            if node.value:
                for target in node.targets:
                    self.visit(target)
                    self.js.write(' = ')
                self.visit(node.value)
            else:
                self.js.write('var ')
                for i, target in enumerate(node.targets):
                    if i != 0:
                        self.js.write(', ')
                    self.visit(target)

    def visit_AugAssign(self, node):
        with self.write_stmt():
            self.visit(node.target)
            self.js.write(' ')
            self.visit(node.op)
            self.js.write('= ')
            self.visit(node.value)

    def visit_Num(self, node):
        self.js.write(str(node.n))

    def visit_Str(self, node):
        self.js.write('"')
        for ch in node.s:
            if ch == '"':
                self.js.write(r'\"')
            else:
                self.js.write(ch)
        self.js.write('"')

    def visit_FunctionDef(self, node):
        with self.write_stmt():
            self.js.write('function ')
            if node.name:
                self.visit(name(node.name))
            self.js.write('(')

            for i, arg in enumerate(node.args.args):
                if i != 0:
                    self.js.write(', ')
                self.js.write(arg.arg)
            self.js.write(')')

            with self.js.block():
                for entry in node.body:
                    self.visit(entry)

    def visit_While(self, node):
        assert not node.orelse
        self.js.indent()
        self.js.write('while (')
        self.visit(node.test)
        self.js.write(')')
        with self.js.block():
            for entry in node.body:
                self.visit(entry)
        self.js.write('\n')

    def visit_If(self, node):
        self.js.indent()
        self.js.write('if (')
        self.visit(node.test)
        self.js.write(')')
        with self.js.block():
            for entry in node.body:
                self.visit(entry)
        if node.orelse:
            self.js.write(' else ')
            with self.js.block():
                for entry in node.orelse:
                    self.visit(entry)
        self.js.write('\n')

    def visit_Try(self, node):
        with self.write_stmt():
            self.js.write('try ')
            with self.js.block():
                for entry in node.body:
                    self.visit(entry)
            self.js.write(' catch (')
            main_name = name(node.handlers[0].name or Context().gensym('exc'))
            self.visit(main_name)
            self.js.write(') ')

            next_orelse = [
                ast.Raise(main_name, None)
            ]
            for handler in reversed(node.handlers):
                body = []
                if handler.name and main_name.id != handler.name:
                    body.append(ast.copy_location(
                        assign(name(handler.name), main_name),
                        handler))
                body += handler.body
                if handler.type:
                    test = _(name('isinstance'))(main_name, handler.type)
                    next_orelse = [ast.copy_location(
                        ast.If(test.node, body, next_orelse),
                        handler)]
                else:
                    next_orelse = body
            with self.js.block():
                for entry in next_orelse:
                    self.visit(entry)

    def visit_Raise(self, node):
        assert not node.cause
        with self.write_stmt():
            self.js.write('throw ')
            self.visit(node.exc)

    def visit_Return(self, node):
        with self.write_stmt():
            self.js.write('return ')
            self.visit(node.value)

    def visit_Call(self, node):
        # Handle javascript injection
        if isinstance(node.func, ast.Name) and node.func.id == '__js__':
            assert len(node.args) == 1
            assert isinstance(node.args[0], ast.Str)
            self.js.write(node.args[0].s)
            return

        self.visit(node.func)
        self.js.write('(')
        for i, arg in enumerate(node.args):
            if i != 0:
                self.js.write(', ')
            self.visit(arg)
        if node.keywords:
            self.visit(ast.copy_location(
                ast.Dict([k.arg for k in node.keywords],
                         [k.value for k in node.keywords]),
                node))
        self.js.write(')')

    def visit_Dict(self, node):
        expand = []
        self.js.write('{')
        for i, (k, v) in enumerate(zip(node.keys, node.values)):
            if i != 0:
                self.js.write(', ')
            self.visit(k)
            self.js.write(': ')
            self.visit(v)
        self.js.write('}')

    def visit_List(self, node):
        self.js.write('[')
        for i, elt in enumerate(node.elts):
            if i != 0:
                self.js.write(', ')
            self.visit(elt)
        self.js.write(']')

    def visit_Tuple(self, node):
        # TODO real tuples?
        return self.visit_List(node)

    def visit_Attribute(self, node):
        self.visit(node.value)
        self.js.write('.')
        self.js.write(node.attr)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.js.write('[')
        self.visit(node.slice)
        self.js.write(']')

    def visit_Index(self, node):
        self.visit(node.value)

    def visit_Name(self, node):
        self.js.write(node.id)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.js.write(' ')
        self.visit(node.op)
        self.js.write(' ')
        self.visit(node.right)

    def visit_UnaryOp(self, node):
        self.visit(node.op)
        self.visit(node.operand)

    def visit_Compare(self, node):
        assert len(node.ops) == 1
        assert len(node.comparators) == 1
        self.visit(node.left)
        self.js.write(' ')
        self.visit(node.ops[0])
        self.js.write(' ')
        self.visit(node.comparators[0])

    def visit_BoolOp(self, node):
        for i, val in enumerate(node.values):
            if i != 0:
                self.js.write(' ')
                self.visit(node.op)
                self.js.write(' ')
            self.visit(val)

    def visit_Add(self, node):
        self.js.write('+')

    def visit_Sub(self, node):
        self.js.write('-')

    def visit_Div(self, node):
        self.js.write('/')

    def visit_Mult(self, node):
        self.js.write('*')

    def visit_Mod(self, node):
        self.js.write('%')

    def visit_LShift(self, node):
        self.js.write('<<')

    def visit_RShift(self, node):
        self.js.write('>>')

    def visit_BitOr(self, node):
        self.js.write('|')

    def visit_BitXor(self, node):
        self.js.write('^')

    def visit_BitAnd(self, node):
        self.js.write('&')

    def visit_UAdd(self, node):
        self.js.write('+')

    def visit_USub(self, node):
        self.js.write('-')

    def visit_Not(self, node):
        self.js.write('!')

    def visit_Invert(self, node):
        self.js.write('~')

    def visit_And(self, node):
        self.js.write('&&')

    def visit_Or(self, node):
        self.js.write('||')

    def visit_Eq(self, node):
        self.js.write('===')

    def visit_NotEq(self, node):
        self.js.write('!==')

    def visit_Lt(self, node):
        self.js.write('<')

    def visit_LtE(self, node):
        self.js.write('<=')

    def visit_Gt(self, node):
        self.js.write('>')

    def visit_GtE(self, node):
        self.js.write('>=')

    def visit_Is(self, node):
        self.js.write('===')

    def visit_IsNot(self, node):
        self.js.write('!==')

    def visit_NameConstant(self, node):
        if node.value in ('None', None):
            self.js.write('null')
        elif node.value in ('True', True):
            self.js.write('true')
        elif node.value in ('False', False):
            self.js.write('false')
        else:
            raise NotImplementedError(node.value)

    def visit_Pass(self, node):
        pass


def to_js(source, *args, **kwargs):
    nodes = ast.parse(source, *args, **kwargs)
    nodes = Simplify().visit(nodes)
    with io.StringIO() as f:
        js = JavaScript('<none>', f)
        visitor = ToJS(js)
        visitor.visit(nodes)
        js.seek(0)
        return js.read()
