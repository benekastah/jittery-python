import os, sys, re, random
import ast
from jittery_python.utils import print_node
from jittery_python.context import Context, ContextStack
from jittery_python.builtins import Builtins

class JSCode:
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return self.code

def compile(text = None, file = None, bare = None):
    compiler = Compiler(input_text = text, input_path = file)
    return compiler.compile(bare = bare)

class CompileError(Exception): pass

class Compiler:
    byte = 1
    kilobyte = 1024 * byte
    megabyte = 1024 * kilobyte
    max_file_size = 100 * megabyte
    default_indent = "  "
    function_ops = (ast.FloorDiv, ast.Pow, ast.Eq, ast.NotEq)
    re_py_ext = re.compile("(\.py)?$")

    def __init__(self, input_path = None, output_path = None, input_text = None, main_compiler = None, module_name = None, print_module_result = False):
        self.indent_level = 0
        self.current_indent = ""

        self.print_module_result = print_module_result

        self.context_stack = ContextStack()

        self.is_main_compiler = not main_compiler
        self.main_compiler = main_compiler

        if input_path:
            (self.input_directory_path, self.input_file_path) = self.get_file_path(input_path, "__init__.py")
            if output_path != False:
                self.output_file_path = output_path or "%s.js" % self.input_file_path
            else:
                self.output_file_path = None
            self.python_path = [self.input_directory_path] + sys.path
            self.input_text = None
        elif input_text:
            self.input_file_path = None
            self.input_directory_path = os.path.abspath('.')
            self.python_path = sys.path
            self.output_file_path = output_path
            self.input_text = input_text
        else:
            raise CompileError("Can't run compiler without either specifying input_path or input_text in the arguments")

        if self.is_main_compiler:
            self.module_name = module_name or "__main__"
            self.modules = []
            self.builtins = Builtins()
        else:
            if not module_name:
                try:
                    module_name = os.path.relpath(self.input_file_path, self.main_compiler.input_directory_path)
                except ValueError:
                    module_name = self.gensym("module").id
                self.module_name = self.re_py_ext.sub("", module_name)
            else:
                self.module_name = module_name

        self.local_module_name = self.gensym(self.module_name, ast.Load())

        if self.is_main_compiler:
            self.main_compiler = self

    def get_file_path(self, path, default_file_name):
        f = None
        d = None
        if path != None and os.path.exists(path):
            path = os.path.abspath(path)
            if os.path.isdir(path):
                f = os.path.join(path, os.path.basename(default_file_name))
                d = path
            elif os.path.isfile(path):
                f = path
                d = os.path.dirname(path)
        return (d, f)

    def indent(self, modify = 0):
        if modify:
            self.indent_level += modify
            if self.indent_level < 0:
                raise CompileError("Indent level can't drop below zero. Current level is %i." % (self.indent_level))
            self.current_indent = "".join([self.default_indent for x in range(self.indent_level)])
        return self.current_indent

    def gensym(self, name = "sym", ctx = ast.Load()):
        name = re.sub("[^\w]", "_", name)
        id = '__%s_%i__' % (name, random.randint(0, 100000))
        return ast.Name(id, ctx)

    def op_is_function(self, op):
        for node_class in self.function_ops:
            if isinstance(op, node_class):
                return True
        return False

    def import_me(self):
        to_call = ast.Name("__import__", ast.Load())
        name = ast.Str(self.module_name)
        args = [name]
        # if self.is_main_compiler:
        #     args.append(ast.Str("builtins"))
        call = ast.Call(to_call, args, None, None, None)
        return self.compile_node(call)

    def compile(self, bare = False, verbose = False):
        self.bare = bare
        self.verbose = verbose

        if self.input_file_path:
            input_f = open(self.input_file_path, 'r')
            python_code = input_f.read(self.max_file_size)
        else:
            python_code = self.input_text
        file_ast = ast.parse(python_code)

        if self.verbose:
            print_node(file_ast)

        self.compile_Module(file_ast)
        if self.is_main_compiler:
            if not self.bare:
                if self.builtins.module_text:
                   self.compile_Import(input_text = self.builtins.module_text, input_name = "builtins")
                import_stmt = self.import_me()
                code = self.modules + [import_stmt]
            else:
                code = self.modules

            compiled = ";\n\n".join(code) + ";\n"
            if not self.bare:
                compiled = "(function () {\n\n" \
                           "%s\n" \
                           "})();" % compiled

            if self.output_file_path:
                output_f = open(self.output_file_path, 'w+')
                output_f.write(compiled)
                output_f.close()
            else:
                return compiled

    def compile_node(self, node, *args):
        if isinstance(node, list):
            f = self.compile_node_list
        else:
            class_name = node.__class__.__name__
            f = getattr(self, "compile_%s" % class_name)
            if not f:
                raise CompileError("No compiler for AST node %s" % class_name)
        return f(node, *args)

    def compile_node_list(self, nodes, joiner = ";\n", trailing = ";"):
        compiled = [self.compile_node(n) for n in nodes]
        result = joiner.join(filter(lambda x: x, compiled))
        if trailing and not result.endswith(trailing):
            result += trailing
        return result

    def compile_statement_list(self, ls):
        return self.compile_node_list(ls, ";\n%s" % self.indent(), ";")

    def compile_Module(self, node):
        self.is_builtins = self.module_name == "builtins"

        body = node.body
        if self.print_module_result:
            try:
                last_body_item = body[-1]
            except IndexError:
                last_body_item = ast.Name("None", ast.Load())
            print_fn = ast.Name("print", ast.Load())
            last_body_item = ast.Call(print_fn, [last_body_item], None, None, None)
            body = body[:-1] + [last_body_item]

        if not self.bare and not self.is_builtins:
            module_name = ast.Str(self.module_name)
            args = ast.arguments([ast.arg(self.local_module_name.id, None)], None, None, None, None, None, None, None)
            func = ast.FunctionDef(name = '', args = args, body = body, decorator_list = [], returns = None)
            to_call = JSCode("__python__.register_module")
            call = ast.Call(to_call, [module_name, func], None, None, None)
            result = self.compile_node(call)
        else:
            context = self.context_stack.new()
            result = self.compile_node(body)
            result = self.compile_statement_list([context.get_vars(True), JSCode(result)])
            self.context_stack.pop()

        if self.is_builtins:
            self.main_compiler.modules = [result] + self.main_compiler.modules
        else:
            self.main_compiler.modules.append(result)

    def compile_Import(self, node = None, input_text = None, input_name = None):
        def do_import(name, input_path = None, input_text = None):
            compiler = Compiler(input_path = input_path, input_text = input_text, main_compiler = self.main_compiler, module_name = input_name)
            compiler.compile()
            import_call = compiler.import_me()
            asname = ast.Name(name, ast.Store())
            assign = ast.Assign([asname], JSCode(import_call))
            return assign

        if node:
            names = node.names
            results = []
            for alias in names:
                name = alias.name
                file_name = "%s.py" % os.path.join(self.input_directory_path, name)
                result = do_import(alias.asname or name, input_path = file_name)
                results.append(result)
            return self.compile_node_list(results, ", ", "")
        elif isinstance(input_text, str):
            if not input_name:
                raise CompileError("Can't compile input_text without input_name")
            assign = do_import(input_name, input_text = input_text)
            return self.compile_node(assign)
        else:
            raise CompileError("Can't import nothing")

    def compile_ImportFrom(self, node):
        module = node.module
        names = node.names
        module_name = self.gensym(module, ast.Load())
        module_alias = ast.alias(module, module_name.id)
        imprt = ast.Import([module_alias])

        results = [imprt]
        for alias in names:
            name = alias.name
            asname = ast.Name(alias.asname or name, ast.Store())
            attr = ast.Attribute(module_name, name, ast.Load())
            assign = ast.Assign([asname], attr)
            results.append(assign)
        return self.compile_node_list(results, ", ", "")

    def compile_Expr(self, node):
        return self.compile_node(node.value)

    def compile_JSCode(self, node):
        return node.code

    jseval_name = "jseval"
    def compile_Call(self, node):
        func = node.func
        args = node.args

        # jseval
        if isinstance(func, ast.Name) and func.id == self.jseval_name:
            arg = args[0]
            if isinstance(arg, ast.Str):
                return arg.s
            else:
                raise CompileError("%s can only be called with a single string argument." % self.jseval_name)
        # Normal function call
        else:
            func = self.compile_node(func)
            args = self.compile_node_list(args, ", ", "")
            return "%s(%s)" % (func, args)

    def compile_ClassCall(self, call):
        return "new %s" % self.compile_node(call)

    def compile_BinOp(self, node):
        op = node.op
        if self.op_is_function(op):
            left = node.left
            right = node.right
            return self.compile_node(ast.Call(op, [left, right], None, None, None))
        else:
            left = self.compile_node(node.left)
            op = self.compile_node(node.op)
            right = self.compile_node(node.right)
            return "%s %s %s" % (left, op, right)

    def compile_UnaryOp(self, node):
        op = node.op
        if self.op_is_function(op):
            operand = node.operand
            return self.compile_node(ast.Call(op, [operand], None, None, None))
        else:
            op = self.compile_node(node.op)
            operand = self.compile_node(node.operand)
            return "%s%s" % (op, operand)

    def compile_BoolOp(self, node):
        op = node.op
        if self.op_is_function(op):
            values = node.values
            return self.compile_node(ast.Call(op, values), None, None, None)
        else:
            op = self.compile_node(node.op)
            return (" %s " % op).join([self.compile_node(x) for x in node.values])

    def compile_Compare(self, node):
        left = node.left
        ops = node.ops
        comparators = node.comparators
        results = []
        for idx, op in enumerate(ops):
            comparator = comparators[idx]
            if self.op_is_function(op):
                result = ast.Call(op, [left, comparator], None, None, None)
                result = self.compile_node(result)
            else:
                result = "%s %s %s" % (self.compile_node(left), self.compile_node(op), self.compile_node(comparator))
            results.append(JSCode(result))
            left = comparator
        bool_op = ast.BoolOp(op = ast.And(), values = results)
        return self.compile_node(bool_op)

    def compile_Assign(self, node, assigner = '='):
        targets = node.targets
        value = node.value

        targets_len = len(targets)
        target0 = targets[0]
        if targets_len > 1 or (isinstance(target0, ast.Tuple) or isinstance(target0, ast.List)):
            if targets_len == 1:
                elts = targets[0].elts
            else:
                elts = targets

            base_name_store = self.gensym("ref", ast.Store())
            base_name = base_name_store.id
            base_name_load = ast.Name(base_name, ast.Load())
            base_assign = ast.Assign([base_name_store], value)

            assignments = [base_assign]
            for idx, target in enumerate(elts):
                index = ast.Index(ast.Num(idx))
                subscript = ast.Subscript(base_name_load, index, ast.Load())
                assign = ast.Assign([target], subscript)
                assignments.append(assign)
            return self.compile_node_list(assignments, ', ', '')
        else:
            target = targets[0]
            c_target = self.compile_node(target)
            c_value = self.compile_node(value)
            return "%s %s %s" % (c_target, assigner, c_value)

    def compile_AugAssign(self, node):
        target = node.target
        op = node.op
        value = node.value
        if self.op_is_function(op):
            left = ast.Name(target.id, ast.Load())
            right = value
            value = ast.BinOp(left = left, op = op, right = right)
            assigner = "="
        else:
            assigner = "%s=" % self.compile_node(op)
        assign = ast.Assign([target], value)
        return self.compile_Assign(assign, assigner)

    def compile_Attribute(self, node, assign = None):
        ctx = node.ctx
        value = self.compile_node(node.value)
        attr = node.attr

        if isinstance(ctx, ast.Store):
            pass
        elif isinstance(ctx, ast.Load):
            pass
        else:
            raise CompileError("Can't compile attribute with context of type %s" % ctx.__class__.__name__)

        return "%s.%s" % (value, attr)

    def compile_Subscript(self, node):
        value = node.value
        slice = node.slice
        if isinstance(slice, ast.Index):
            return "%s%s" % (self.compile_node(value), self.compile_node(slice))
        elif isinstance(slice, ast.Slice):
            return self.compile_Slice(slice, value = value)
        else:
            raise CompilerError("Can't compile subscript unless the slice node is either ast.Index or ast.Slice")


    def compile_Index(self, node):
        return "[" + self.compile_node(node.value) + "]"

    def compile_Slice(self, node, value):
        _None = ast.Name("None", ast.Load())
        lower = node.lower or _None
        upper = node.upper or _None
        step = node.step or _None
        fn = ast.Name("__slice__", ast.Load())
        call = ast.Call(fn, [value, lower, upper, step], None, None, None)
        return self.compile_node(call)

    # Binary operators
    def compile_Add(self, node):
        return "+"

    def compile_Sub(self, node):
        return "-"

    def compile_Div(self, node):
        return "/"

    def compile_FloorDiv(self, node):
        return "__python__.__floor_div__"

    def compile_Mult(self, node):
        return "*"

    def compile_Pow(self, node):
        return "Math.pow"

    def compile_Mod(self, node):
        return "%"

    # Boolean operators
    def compile_Or(self, node):
        return "||"

    def compile_And(self, node):
        return "&&"

    def compile_Not(self, node):
        return "!"

    # Unary operators
    def compile_USub(self, node):
        return "-"

    def compile_UAdd(self, node):
        return "+"

    # Bitwise operators
    def compile_Invert(self, node):
        return "~"

    def compile_RShift(self, node):
        return ">>>"

    def compile_LShift(self, node):
        return "<<"

    def compile_BitAnd(self, node):
        return "&"

    def compile_BitOr(self, node):
        return "|"

    def compile_BitXor(self, node):
        return "^"

    # Comparison operators
    def compile_Eq(self, node):
        name = ast.Name("__eq__", ast.Load())
        return self.compile_node(name)

    def compile_NotEq(self, node):
        name = ast.Name("__eq__", ast.Load())
        return "!%s" % self.compile_node(name)

    def compile_Gt(self, node):
        return ">"

    def compile_GtE(self, node):
        return ">="

    def compile_Lt(self, node):
        return "<"

    def compile_LtE(self, node):
        return "<="

    def compile_Is(self, node):
        return "==="

    def compile_IsNot(self, node):
        return "!=="

    def compile_Pass(selfe, node):
        return None

    # Primitives
    def compile_Num(self, node):
        n = str(node.n)
        return n

    re_dblquote = re.compile(r'"')
    def compile_Str(self, node):
        escaped = re.sub(self.re_dblquote, r'\"', node.s)
        return '"%s"' % escaped

    javascript_reserved_words = (
        "break",
        "case",
        "catch",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "finally",
        "for",
        "function",
        "if",
        "in",
        "instanceof",
        "new",
        "return",
        "switch",
        "this",
        "throw",
        "try",
        "typeof",
        "var",
        "void",
        "while",
        "with",
        "class",
        "enum",
        "export",
        "extends",
        "import",
        "super",
        "implements",
        "interface",
        "let",
        "package",
        "private",
        "protected",
        "public",
        "static",
        "yield",
    )

    python_keywords = {
        'True': 'true',
        'False': 'false',
        'None': 'null',
    }

    def compile_Name(self, node):
        id = node.id
        ctx = node.ctx

        if id in self.python_keywords:
            return self.python_keywords[id]

        is_super = id == "super"
        if id in self.javascript_reserved_words:
            id = "$%s" % id
            node = ast.Name(id, ctx)

        try:
            active_ctx = self.context_stack.find(node)
        except IndexError:
            active_ctx = None

        if active_ctx and isinstance(ctx, ast.Store):
            active_ctx.set(node)

        is_local_module_name = node is self.local_module_name
        if is_super:
            return "__self__.%s" % id
        elif not is_local_module_name and not self.is_builtins and active_ctx and active_ctx.is_module_context() and active_ctx.get(node):
            local_module_name = self.compile_node(self.local_module_name)
            return "%s.%s" % (local_module_name, id)
        elif active_ctx and active_ctx.is_class_context() and active_ctx.get(node):
            return "%s.%s.%s" % (active_ctx.class_name, "prototype", id)
        else:
            self.main_compiler.builtins.use(id)
            return id

    def compile_If(self, node):
        indent0 = self.indent()
        indent1 = self.indent(1)

        test = self.compile_node(node.test)
        body = self.compile_statement_list(node.body)
        if node.orelse:
            orelse = self.compile_statement_list(node.orelse)
            orelse = " else {\n%(indent1)s%(orelse)s\n%(indent0)s}" % {'orelse': orelse, 'indent0': indent0, 'indent1': indent1}
        else:
            orelse = ''

        self.indent(-1)

        return 'if (%(test)s) {\n%(indent1)s%(body)s\n%(indent0)s}%(orelse)s' % {'test': test, 'body': body, 'orelse': orelse, 'indent0': indent0, 'indent1': indent1}

    def compile_While(self, node):
        test = node.test
        body = node.body
        orelse = node.orelse

        indent0 = self.indent()
        indent1 = self.indent(1)

        if orelse:
            _if = ast.If(test, orelse)
            body = body + [_if]

        result = ("while (%(test)s) {\n"
                  "%(indent1)s%(body)s\n"
                  "%(indent0)s}") % {
                      'test': self.compile_node(test),
                      'body': self.compile_statement_list(body),
                      'indent0': indent0,
                      'indent1': indent1,
                  }

        self.indent(-1)
        return result

    def compile_For(self, node):
        indent0 = self.indent()
        indent1 = self.indent(1)

        target = node.target
        iter = node.iter
        body = node.body
        orelse = node.orelse

        iter_store = self.gensym("iter", ast.Store())
        iter_load = ast.Name(iter_store.id, ast.Load())
        counter_store = self.gensym('i', ast.Store())
        counter_load = ast.Name(counter_store.id, ast.Load())
        len_store = self.gensym('len', ast.Store())
        len_load = ast.Name(len_store.id, ast.Load())
        for_condition = "(%(counter_store)s = 0, %(iter_store)s = %(iter)s, %(len_store)s = %(iter_load)s.length;" \
                        " %(counter_load)s < %(len_load)s;" \
                        " %(counter_store)s++)" % {
                            'counter_store': self.compile_node(counter_store),
                            'counter_load': self.compile_node(counter_load),
                            'len_store': self.compile_node(len_store),
                            'len_load': self.compile_node(len_load),
                            'iter': self.compile_node(iter),
                            'iter_store': self.compile_node(iter_store),
                            'iter_load': self.compile_node(iter_load),
                        }

        target_assign = ast.Assign([target], ast.Subscript(iter_load, ast.Index(counter_load), ast.Load()))
        body = [target_assign] + body
        if orelse:
            _if = ast.If(ast.BinOp(counter_load, ast.Eq(), len_load), orelse)
            body = body + [_if]

        result = 'for %(for_condition)s {\n%(indent1)s%(body)s\n%(indent0)s}' % {
            'for_condition': for_condition,
            'indent0': indent0,
            'indent1': indent1,
            'body': self.compile_statement_list(body)
        }

        self.indent(-1)
        return result

    def compile_ListComp(self, node):
        elt = node.elt
        generators = node.generators

        result_name = self.gensym("result", ast.Store())
        result_assign = ast.Assign([result_name], ast.List([], ast.Store()))
        result_name = ast.Name(result_name.id, ast.Load())

        append_result = ast.Call(ast.Attribute(result_name, "push", ast.Load()), [elt], None, None, None)
        body = append_result
        for generator in reversed(generators):
            ifs = generator.ifs
            compare = None
            for _if in ifs:
                if not compare:
                    compare = _if
                else:
                    compare = ast.BinOp(compare, ast.And(), _if)
            if compare:
                body = ast.If(compare, [body], None)

            body = ast.For(generator.target, generator.iter, [body], None)

        ret = ast.Return(result_name)
        func = ast.FunctionDef(None, [], [result_assign, body, ret], None, None)
        call = ast.Call(func, [], None, None, None)
        return self.compile_node(call)

    def compile_Raise(self, node):
        exc = node.exc
        cause = node.cause
        return "throw %s" % self.compile_node(exc)

    def compile_Global(self, node):
        ctx = self.context_stack[-1]
        for name in node.names:
            ctx.set_global(name)

    def compile_Dict(self, node):
        keys = self.compile_node(ast.List(node.keys, ast.Load()))
        values = self.compile_node(ast.List(node.values, ast.Load()))
        dictcls = ast.Name('dict', ast.Load())
        call = ast.Call(dictcls, [keys, values], None, None, None)
        return self.compile_ClassCall(call)

    def compile_Array(self, node_list):
        elts = self.compile_node_list(node_list, ", ", "")
        return "[%s]" % elts

    def compile_List(self, node):
        return self.compile_Array(node.elts)

    def compile_Tuple(self, node):
        tuplecls = ast.Name('tuple', ast.Load())
        call = ast.Call(tuplecls, [JSCode(self.compile_Array(node.elts))], None, None, None)
        return self.compile_ClassCall(call)

    def compile_Lambda(self, node):
        ret = ast.Return(node.body)
        func = ast.FunctionDef(name = None, args = node.args, body = [ret], decorator_list = None)
        return self.compile_node(func)

    def compile_FunctionDef(self, node, class_name = None, true_named_function = False):
        # Compile the function name outside of the function context.
        is_class_fn = False
        if node.name:
            name = ast.Name(node.name, ast.Store())
            ctx = self.context_stack.find(name)
            is_class_fn = ctx.is_class_context()
            c_name = self.compile_node(name)
            name = JSCode(c_name)
        else:
            name = None

        has_super = False
        if is_class_fn:
            for body_node in node.body:
                for child_node in ast.walk(body_node):
                    if isinstance(child_node, ast.Name) and child_node.id in ('super', '$super'):
                        has_super = True
                        break

        ctx = self.context_stack.new(class_name = class_name)
        indent0 = self.indent()
        indent1 = self.indent(1)

        print("Warning: functions can't handle varargs or kwargs yet")
        if node.args:
            node_args = node.args
            # vararg = node_args.vararg
            args = []
            for arg in node_args.args:
                a = arg.arg
                ctx.set_argument(a)
                args.append(a)
            args = ', '.join(args)
        else:
            args = ''

        # decorator_list = node.decorator_list
        # returns = node.returns

        body = node.body
        if has_super:
            _self = ast.Name("__self__", ast.Store())
            _self_assign = ast.Assign([_self], JSCode("arguments[0]"))
            body = [_self_assign] + body

        body = self.compile_statement_list(body)
        declare_locals = ctx.get_vars()
        body = self.compile_statement_list([declare_locals, JSCode(body)])

        if true_named_function:
            true_fn_name = name or ""
        else:
            true_fn_name = ""

        value = ("function %s(%s) {\n%s"
                 "%s\n"
                 "%s}") % (true_fn_name, args, indent1, body, indent0)
        self.context_stack.pop()

        self.indent(-1)

        if name:
            targets = [name]
            assign = ast.Assign(targets, JSCode(value))
            return self.compile_node(assign)
        else:
            return value

    def compile_Return(self, node):
        return "return %s" % self.compile_node(node.value)

    def compile_ClassDef(self, node):
        name = node.name
        body = node.body

        instantiate = ast.Name("__class_instantiate__", ast.Load())
        instantiate_call = ast.Call(instantiate, [JSCode("this"), JSCode("arguments")], None, None, None)
        ret = ast.Return(instantiate_call)
        cls = ast.FunctionDef(name, [], [ret], None, None)
        self.indent(1)
        cls = JSCode(self.compile_FunctionDef(cls, true_named_function = True))
        self.indent(-1)

        if not node.bases:
            node.bases = [ast.Name('object', ast.Load())]
        elif len(node.bases) > 1:
            raise CompileError("Multiple inheritance is not currently supported")

        basename = node.bases[0]
        func = ast.Name("__class_extend__", ast.Load())
        base = ast.Call(func, [JSCode(name), basename], None, None, None)

        ret = ast.Return(JSCode(name))
        func = ast.FunctionDef(name = None, args = None, body = [base, cls] + body + [ret])
        func = JSCode(self.compile_FunctionDef(func, class_name = name))
        call = ast.Call(func, [], None, None, None)
        cls_name = ast.Name(name, ast.Store())
        assign = ast.Assign([cls_name], call)
        return self.compile_node(assign)
