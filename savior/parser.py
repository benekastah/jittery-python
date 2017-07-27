from contextlib import contextmanager
import ast
import enum
import io
import random
import sys

from savior.builder import ASTBuilder as _
from savior.builder import name, assign, new_scope, arguments
from savior.util import parse_expr


def extend(ls, nodes):
    try:
        it = iter(nodes)
    except TypeError:
        it = [nodes]
    return ls.extend(list(it))


class Context:

    _global_context = None

    def __init__(self, parent=None, base_obj=None):
        self.vars = set()
        self.novars = set()
        self.parent = parent
        self.base_obj = base_obj
        self.is_module = False

    def __contains__(self, var):
        return self.has_var(var) or var in (self.parent or set())

    def has_var(self, var):
        return var in self.vars or var in self.novars

    def add_var(self, var):
        self.vars.add(var)
        return var

    def add_novar(self, arg):
        self.novars.add(arg)
        return arg

    def gensym(self, name='', no_var=False):
        sym = '${}'.format(name)
        i = 1
        while sym in self:
            sym = '${}{}'.format(name, i)
            i += 1
        if no_var:
            self.add_novar(sym)
        else:
            self.add_var(sym)
        return sym

    @staticmethod
    def is_gensym(name):
        return name.startswith('$')

    def merge(self, context):
        self.vars |= context.vars
        self.novars |= context.novars

    def __repr__(self):
        me = repr(self.vars | self.novars)
        if self.base_obj:
            me = '{} = {}'.format(ast.dump(self.base_obj), me)
        if self.parent:
            me = '{} -> {}'.format(repr(self.parent), me)
        return me

    @classmethod
    def get_global_context(cls):
        if not Context._global_context:
            Context._global_context = Context()
        return Context._global_context


class JavaScript:

    def __init__(self, fname, module_name, file):
        self.fname = fname
        self.module_name = module_name
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

    def __init__(self, fname, module_name):
        super().__init__()
        self.fname = fname
        self.module_name = module_name
        self.module_context = None
        self.context = Context.get_global_context()
        self.star_imports = []

    @contextmanager
    def _block(self, base_obj=None):
        self.context = Context(self.context, base_obj)
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

    def _assign_from_context(self):
        should_expand = self.context.is_module or not self.context.base_obj
        vars_ = [name(v) for v in self.context.vars if should_expand or Context.is_gensym(v)]
        if vars_:
            return assign(vars_, None)

    def _assign(self, a, b):
        result = self.visit(assign(a, _(None).node))
        return assign(result.targets, b)

    def visit_Module(self, node):
        def is_bare(node):
            if node.body and isinstance(node.body[0], ast.Expr):
                val = node.body[0].value
                if isinstance(val, ast.Str) and val.s.strip() == 'bare module':
                    return True
            return False

        module_var = self.context.gensym('module')
        self.star_imports.append(module_var)
        with self._block(name(module_var)):
            self.context.is_module = True
            self.context.add_novar(module_var)
            body = []
            if not is_bare(node):
                body.append(ast.ImportFrom('builtins', [ast.alias(name='*', asname=None)], 0))
            module_name_str = ast.Str(self.module_name)
            body.extend([
                assign(name('__module__'), name(module_var)),
                assign(name('__name__'), module_name_str),
                assign(name('__file__'), ast.Str(self.fname))
            ])
            body.extend(node.body)
            body.append(ast.Return(name(module_var)))
            module = ast.copy_location(
                _(name('JITTERY')).register_module(
                    ast.Str(self.fname),
                    module_name_str,
                    ast.FunctionDef(None, arguments(args=[ast.arg(module_var, None)]), body,
                                    [], None)).node,
                node)
            return self.visit(module)

    def _assign_import(self, alias, result):
        assert alias.name != '*', 'Star imports not supported'
        parts = (alias.asname or alias.name).split('.')
        assignee = None
        for i, part in enumerate(parts):
            if not assignee:
                self.context.add_var(part)
                assignee = name(part)
            else:
                assignee = _(assignee).attr(part).node
            if i < len(parts) - 1:
                assignment = _(assignee).or_({}).node
            else:
                assignment = result
            yield self.visit(assign(assignee, assignment))

    def visit_ImportFrom(self, node):
        nodes = []
        result = _(name('JITTERY')).__import__(node.module, None, None, [
            alias.name for alias in node.names
        ], node.level).node
        imprt = name(self.context.gensym('import'))
        nodes.append(self.visit(ast.copy_location(
            assign(imprt, result), node)))
        for alias in node.names:
            if alias.name == '*':
                self.star_imports.append(node.module)
                alias = ast.alias(node.module, None)
            extend(nodes, self._assign_import(alias, imprt))
        return nodes

    def visit_Import(self, node):
        nodes = []
        for alias in node.names:
            result = _(name('JITTERY')).__import__(name(alias.name), None, None, [], 0).node
            imprt = name(self.context.gensym('import'))
            nodes.append(self.visit(ast.copy_location(
                assign(imprt, result), node)))
            extend(nodes, self._assign_import(alias, imprt))
        return nodes

    def visit_FunctionDef(self, node):
        assert not node.args.kwonlyargs
        assert not node.args.kw_defaults

        if getattr(node, '__new_scope', False):
            return self.generic_visit(node)

        is_module = self.context.is_module
        is_new_scope = getattr(node, '__new_scope', False)

        @contextmanager
        def _block():
            if self.context.is_module:
                context = self.context
                with self._block(self.context.base_obj):
                    self.context.merge(context)
                    context = self.context
                    yield
                self.context.merge(context)
            else:
                with self._block():
                    yield

        def _assign_from_context(body):
            var_assignment = self._assign_from_context()
            if var_assignment:
                body.insert(0, ast.copy_location(var_assignment, node))

        is_expr = not node.name
        fn_name = name(self.context.gensym('fn', no_var=True))
        self.context.add_novar(fn_name.id)
        with _block():
            body = []
            if not is_new_scope:
                args_ = name(self.context.gensym('args', no_var=True))
                kwarg = None
                if node.args.kwarg:
                    kwarg = name(self.context.add_novar(node.args.kwarg.arg))


                defaults = [None] * (len(node.args.args) - len(node.args.defaults))
                defaults += node.args.defaults
                assert len(defaults) == len(node.args.args)

                for i, (arg, default) in enumerate(zip(node.args.args, defaults)):
                    val = _(args_)[i].node
                    if default:
                        val = ast.IfExp((_(name('len'))(args_) > i).node, val, default)
                    extend(body, self.visit(ast.copy_location(assign(name(arg.arg), val), node)))

                if node.args.vararg:
                    body.append(self.visit(ast.copy_location(
                        assign(
                            name(node.args.vararg.arg),
                            _(name('Array')).prototype.slice.call(
                                args_, len(node.args.args)
                            ).node),
                        node.args.vararg)))

                if node.args.kwarg:
                    get_kwarg = assign(kwarg, _(kwarg).or_({}).node)
                    body.append(self.visit(ast.copy_location(get_kwarg, node.args.kwarg)))

            node = self.generic_visit(node)

            # Do this after processing other args
            if not is_module:
                _assign_from_context(body)

            body.extend(node.body)

        # Assign from context again for module stuff
        if is_module:
            _assign_from_context(body)

        new_args = arguments(args=(
            [ast.arg(args_.id, None)] + ([ast.arg(kwarg.id, None)] if kwarg else [])))

        fn = ast.copy_location(
            ast.FunctionDef(fn_name.id, new_args, body, [], node.returns),
            node)

        if is_new_scope:
            return fn
        else:
            assign_call = ast.copy_location(
                self.visit(assign(_(fn_name).attr('__call__').node, fn_name)),
                node)

            nodes = [fn]
            fn = self._decorate(fn_name, node.decorator_list)
            if node.name:
                extend(nodes, ast.copy_location(
                    self._assign(name(node.name), fn),
                    node))
            extend(nodes, assign_call)

            if is_expr:
                return ast.copy_location(new_scope(nodes, fn_name), node)
            else:
                return nodes

    def visit_ClassDef(self, node):
        assert len(node.bases) <= 1
        assert not node.keywords

        nodes = []

        with self._block():
            # Keep a reference to the original class so that reassigning to
            # node.name doesn't affect our ability to instantiate
            saved_cls = name(self.context.gensym(node.name))
            nodes.append(
                self.visit(ast.copy_location(
                    assign(saved_cls, None),
                    node)))

            __js__ = _(name('__js__'))
            this = self.context.gensym('self')
            makeself = assign(name(this), __js__('Object.create({}.prototype)'.format(saved_cls.id)).node)

            keyname = name(self.context.gensym('key'))
            fnname = name(self.context.gensym('fn'))
            bindall = __js__('JITTERY.bindall({})'.format(this)).node

            extend(nodes, self.visit(ast.copy_location(
                ast.FunctionDef(
                    saved_cls.id,
                    arguments(), [
                        makeself,
                        assign(_(name(this)).attr('__class__').node, saved_cls),
                        ast.Expr(bindall),
                        ast.Expr(__js__('{0}.__init__ && {0}.__init__.apply(null, arguments)'.format(this)).node),
                        ast.Return(name(this))
                    ],
                    node.decorator_list,
                    None), node)))

            extend(nodes, self.visit(ast.copy_location(
                assign(_(saved_cls).attr('__name__').node, ast.Str(node.name)),
                node)))

            if node.bases:
                nodes.append(self.visit(ast.copy_location(
                    assign(
                        _(saved_cls).prototype.node,
                        _(name('Object')).create(_(node.bases[0]).prototype).node),
                    node)))

            with self._block(_(saved_cls).prototype.node):
                for entry in node.body:
                    extend(nodes, self.visit(entry))

        return ast.copy_location(
            self._assign(name(node.name), new_scope(nodes, saved_cls)), node)

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
        extend(nodes, self.visit(ast.copy_location(
            assign(it, _(name('iter'))(node.iter).node),
            node)))
        extend(nodes, self.visit(ast.copy_location(
            assign(running, _(True).node),
            node)))
        body = ast.copy_location(ast.Try([
            ast.copy_location(
                assign(node.target, _(name('next'))(it).node),
                node),
            *node.body
        ], [ast.ExceptHandler(name('StopIteration'), None, [
            assign(running, _(False).node)
        ])], [], []), node)
        extend(nodes, self.visit(ast.copy_location(
            ast.While(running, [body], node.orelse),
            node)))
        return nodes

    def visit_While(self, node):
        nodes = []

        body = []
        if node.orelse:
            br = self._gensym('break')
            body.append(assign(br, _(True).node))
        extend(body, node.body)
        if node.orelse:
            body.append(assign(br, _(False).node))

        nodes.append(ast.copy_location(
            ast.While(node.test, body, []),
            node))

        if node.orelse:
            nodes.append(ast.copy_location(
                ast.If(ast.UnaryOp(ast.Not(), br), node.orelse, []),
                node.orelse[0]))

        return [self.generic_visit(n) for n in nodes]

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.context.add_var(node.id)

        if Context.is_gensym(node.id) or node.id in ('this', '__js__', 'JITTERY'):
            # These vars are autogenerated, don't need special treatment
            return node

        context = self.context
        while context:
            if context.has_var(node.id):
                if context.base_obj:
                    return ast.copy_location(
                        _(context.base_obj).attr(node.id).node,
                        node)
                else:
                    return node
            context = context.parent

        def _parse_expr(module):
            if Context.is_gensym(module):
                return name(module)
            else:
                return parse_expr(module)

        # Not found
        obj = _(node)
        for module in self.star_imports:
            module_expr = _(_parse_expr(module)).attr(node.id).node
            obj = _(self.visit(module_expr)).or_(obj)
        return ast.copy_location(obj.node, node)

    def visit_Compare(self, node):
        node = self.generic_visit(node)
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

        return ast.copy_location(
            ast.BoolOp(ast.And(), comparisons),
            node)

    def visit_Call(self, node):
        node = self.generic_visit(node)
        fn_name = node.func.id if isinstance(node.func, ast.Name) else None
        if fn_name == '__js__':
            return node

        if node.keywords:
            kwargs = self.visit(ast.copy_location(
                ast.Dict([ast.Str(k.arg) for k in node.keywords],
                         [k.value for k in node.keywords]),
                node))
        else:
            kwargs = _(None).node

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

        if not args:
            args = ast.List([], ast.Load())

        this = node.func.value if isinstance(node.func, ast.Attribute) else _(None).node
        return ast.copy_location(
            _(name('__js__'))('JITTERY.__call__').call(this, node.func, args, kwargs).node,
            node)

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
            node = self.visit(ast.copy_location(new_scope(body, d), node))

        return node

    def visit_Try(self, node):
        node = self.generic_visit(node)
        main_name = name(node.handlers[0].name or self.context.gensym('exc'))
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
        next_orelse = [self.visit(n) for n in next_orelse]
        return ast.copy_location(
            ast.Try(node.body, [ast.ExceptHandler(None, main_name, next_orelse)], node.orelse, node.finalbody),
            node)

    def visit_Assign(self, node):
        node = self.generic_visit(node)

        ordinary = []
        to_unpack = []
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                to_unpack.append(target)
            else:
                ordinary.append(target)

        if not to_unpack:
            return node

        tmp = name(self.context.gensym('tmp'))
        nodes = [assign(tmp, node.value)]
        if ordinary:
            nodes.append(assign(ordinary, node.value))

        starred = None
        for target in to_unpack:
            for i, entry in enumerate(target.elts):
                if isinstance(entry, ast.Starred):
                    starred = [entry, i, None]
                    continue
                elif starred:
                    starred[2] = i
                    extend(nodes, self.visit(assign(entry, _(tmp)[_(tmp).length - i].node)))
                else:
                    extend(nodes, self.visit(assign(entry, _(tmp)[i].node)))

        if starred:
            entry, start, end = starred
            val = None
            if end:
                val = _(tmp).slice(start, end)
            else:
                val = _(tmp).slice(start)
            extend(nodes, self.visit(assign(entry, val)))

        return nodes


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
    def _write_stmt(self):
        if self.in_expr[-1]:
            self.js.write('(')
            yield
            self.js.write(')')
        else:
            with self.js.line(';'):
                yield

    def visit_Expr(self, node):
        with self._write_stmt():
            self.visit_children(node)

    def visit_Assign(self, node):
        with self._write_stmt():
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
        with self._write_stmt():
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
            if ch in ('"', '\n', '\r'):
                self.js.write('\\')
                self.js.write(ch)
            else:
                self.js.write(ch)
        self.js.write('"')

    def visit_FunctionDef(self, node):
        with self._write_stmt():
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
                self.visit(ast.Expr(ast.Str('use strict')))
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

    def visit_IfExp(self, node):
        self.js.write('((')
        self.visit(node.test)
        self.js.write(') ? (')
        self.visit(node.body)
        self.js.write(') : (')
        self.visit(node.orelse)
        self.js.write('))')

    def visit_Try(self, node):
        assert len(node.handlers) == 1
        assert node.handlers[0].type == None
        assert isinstance(node.handlers[0].name, ast.Name)

        # TODO implement these
        assert not node.orelse
        assert not node.finalbody

        handler, = node.handlers

        with self._write_stmt():
            self.js.write('try')
            with self.js.block():
                for entry in node.body:
                    self.visit(entry)
            self.js.write(' catch (')
            self.visit(handler.name)
            self.js.write(')')
            with self.js.block():
                for entry in handler.body:
                    self.visit(entry)

    def visit_Raise(self, node):
        assert not node.cause
        with self._write_stmt():
            self.js.write('throw ')
            self.visit(node.exc)

    def visit_Return(self, node):
        with self._write_stmt():
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
        self.js.write('(')
        assert len(node.ops) == 1
        assert len(node.comparators) == 1
        self.visit(node.left)
        self.js.write(' ')
        self.visit(node.ops[0])
        self.js.write(' ')
        self.visit(node.comparators[0])
        self.js.write(')')

    def visit_BoolOp(self, node):
        assert len(node.values) > 1
        self.js.write('(')
        for i, val in enumerate(node.values):
            if i != 0:
                self.js.write(' ')
                self.visit(node.op)
                self.js.write(' ')
            self.visit(val)
        self.js.write(')')

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

    def visit_Break(self, node):
        with self._write_stmt():
            self.js.write('break')


def to_js(fname, module_name, outfile):
    with open(fname) as f:
        nodes = ast.parse(f.read(), filename=fname)
        nodes = Simplify(fname, module_name).visit(nodes)
        js = JavaScript(fname, module_name, outfile)
        visitor = ToJS(js)
        visitor.visit(nodes)
        js.write('\n')
