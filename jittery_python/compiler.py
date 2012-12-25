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

    def __init__(self, input_path = None, output_path = None, input_text = None, main_compiler = None, module_name = None):
        self.indent_level = 0
        self.current_indent = ""

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
        if trailing:
            result += trailing
        return result

    def compile_statement_list(self, ls):
        return self.compile_node_list(ls, ";\n%s" % self.indent(), ";")

    def compile_Module(self, node):
        self.is_builtins = self.module_name == "builtins"

        if not self.bare and not self.is_builtins:
            module_name = ast.Str(self.module_name)
            args = ast.arguments([ast.arg(self.local_module_name.id, None)], None, None, None, None, None, None, None)
            func = ast.FunctionDef(name = '', args = args, body = node.body, decorator_list = [], returns = None)
            to_call = JSCode("__python__.register_module")
            call = ast.Call(to_call, [module_name, func], None, None, None)
            result = self.compile_node(call)
        else:
            self.context_stack.new()
            result = self.compile_node(node.body)
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
            if isinstance(target, ast.Attribute):
                return self.compile_Attribute(target, value)
            else:
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
        to_call = ast.Attribute(value, "__getitem__", ast.Load())
        call = ast.Call(to_call, [slice], None, None, None)
        return self.compile_node(call)

    def compile_Index(self, node):
        return self.compile_node(node.value)

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
        name = ast.Name("eq", ast.Load())
        return self.compile_node(name)

    def compile_NotEq(self, node):
        name = ast.Name("eq", ast.Load())
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

        if isinstance(ctx, ast.Store):
            try:
                active_ctx = self.context_stack[-1]
                if active_ctx.is_global(node):
                    active_ctx = self.context_stack[0]
                    active_ctx.set(node)
            except IndexError:
                active_ctx = None
        else:
            active_ctx = self.context_stack.find(node) or (self.context_stack and self.context_stack[0])

        is_local_module_name = node is self.local_module_name
        if not is_local_module_name and active_ctx and active_ctx.is_module_context() and active_ctx.get(node):
            local_module_name = self.compile_node(self.local_module_name)
            return "%s.%s" % (local_module_name, id)
        elif not is_super and active_ctx and active_ctx.is_class_context() and active_ctx.get(node):
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
        elts = self.compile_node_list(node.elts, ", ", "")
        return "[%s]" % elts

    def compile_List(self, node):
        listcls = ast.Name('list', ast.Load())
        call = ast.Call(listcls, [self.compile_Array(node.elts)], None, None, None)
        return self.compile_ClassCall(call)

    def compile_Tuple(self, node):
        tuplecls = ast.Name('tuple', ast.Load())
        call = ast.Call(tuplecls, [self.compileArray(node.elts)], None, None, None)
        return self.compile_ClassCall(call)

    def compile_Lambda(self, node):
        ret = ast.Return(node.body)
        func = ast.FunctionDef(name = None, args = node.args, body = [ret], decorator_list = None)
        return self.compile_node(func)

    def compile_FunctionDef(self, node, class_name = None):
        ctx = self.context_stack.new(class_name = class_name)
        indent0 = self.indent()
        indent1 = self.indent(1)

        if node.args:
            args = []
            for arg in node.args.args:
                a = arg.arg
                ctx.set_argument(a)
                args.append(a)
            args = ', '.join(args)
        else:
            args = ''
        body = self.compile_statement_list(node.body)

        declare_locals = ", ".join(ctx.locals)
        if declare_locals:
            declare_locals = "%svar %s;\n" % (indent1, declare_locals)

        value = ("function (%s) {\n%s"
                 "%s%s\n"
                 "%s}") % (args, declare_locals, indent1, body, indent0)
        self.context_stack.pop()

        self.indent(-1)

        if node.name:
            targets = [ast.Name(node.name, ast.Store())]
            assign = ast.Assign(targets, JSCode(value))
            return self.compile_node(assign)
        else:
            return value

    def compile_Return(self, node):
        return "return %s" % self.compile_node(node.value)

    def compile_ClassDef(self, node):
        name = node.name
        body = node.body
        objectname = self.compile_node(ast.Name("object", ast.Load()))
        cls = JSCode("function %s() { return %s.call(this, arguments); }" % (name, objectname))

        if node.bases:
            basename = node.bases[0]
            func = JSCode("%s.extend" % objectname)
            base = ast.Call(func, [JSCode(name), basename], None, None, None)
            sup = JSCode("%s.prototype" % self.compile_node(basename))
        else:
            base = JSCode("")
            sup = JSCode("%s.prototype" % self.compile_node(ast.Name("object", ast.Load())))

        supname = [ast.Name("super", ast.Store())]
        suplambda = ast.Lambda(args = [], body = sup)
        supassign = ast.Assign(supname, suplambda)

        ret = ast.Return(JSCode(name))
        func = ast.FunctionDef(name = None, args = None, body = [base, supassign, cls] + body + [ret])
        func = JSCode(self.compile_FunctionDef(func, class_name = name))
        call = ast.Call(func, [], None, None, None)
        cls_name = ast.Name(name, ast.Store())
        assign = ast.Assign([cls_name], call)
        return self.compile_node(assign)
