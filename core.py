import os, sys, pprint, re, random
import ast

def print_node(node):
    print(ast.dump(node))


class JSCode:
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return self.code


class Context:
    def __init__(self, stack, class_name = None):
        self.stack = stack
        self.class_name = class_name
        self.globals = []
        self.arguments = []
        self.locals = []

    def get_key_id(self, key):
        if isinstance(key, str):
            return key
        elif isinstance(key, ast.Name):
            return key.id
        else:
            raise Exception("Invalid key: %s" % str(key))

    def get(self, key):
        id = self.get_key_id(key)
        return id in self.locals or id in self.arguments

    def set(self, key, include = True, ls = None):
        if ls is None:
            ls = self.locals

        if ls is self.locals:
            other_ls = self.arguments
        else:
            other_ls = self.locals

        id = self.get_key_id(key)
        already_in_ls = id in ls
        already_in_other = id in other_ls

        if include and (self.is_module_context() or id not in self.globals) and not already_in_other and not already_in_ls:
            ls.append(id)
        elif not include and already_in_ls:
            index = ls.index(id)
            del ls[index]

    def set_global(self, key):
        id = self.get_key_id(key)
        if id in self.locals:
            self.set(id, False)
            print("SyntaxWarning: name '%s' is assigned to before global declaration" % id)

        self.globals.append(id)

    def is_global(self, key):
        id = self.get_key_id(key)
        return id in self.globals

    def set_argument(self, arg):
        self.set(arg, ls = self.arguments)

    def is_module_context(self):
        return self is self.stack[0]

    def is_class_context(self):
        return not not self.class_name


class ContextStack(list):
    def new(self, class_name = None):
        ctx = Context(self, class_name)
        self.append(ctx)
        return ctx

    def find(self, name):
        id = name.id
        for ctx in reversed(self):
            if ctx.get(id):
                return ctx


class Compiler:
    byte = 1
    kilobyte = 1024 * byte
    megabyte = 1024 * kilobyte
    max_file_size = 100 * megabyte
    default_indent = "  "
    function_ops = (ast.FloorDiv, ast.Pow, ast.Eq, ast.NotEq)

    def __init__(self, input_path, main_compiler = None):
        self.indent_level = 0
        self.current_indent = ""

        self.context_stack = ContextStack()

        self.is_main_compiler = not main_compiler
        self.main_compiler = main_compiler

        (self.input_directory_path, self.input_file_path) = self.get_file_path(input_path, "__init__.py")
        self.output_file_path = "%s.js" % self.input_file_path
        self.python_path = [self.input_directory_path] + sys.path

        if self.is_main_compiler:
            self.module_name = "__main__"
            self.modules = []
        else:
            module_name = os.path.relpath(self.input_file_path, self.main_compiler.input_directory_path)
            self.module_name = re.sub("(\.py)?$", "", module_name)

        self.local_module_name = self.gensym(self.module_name, ast.Load())

        if self.is_main_compiler:
            self.main_compiler = self
        self.compile()

    def get_file_path(self, path, default_file_name):
        file = dir = None
        if path != None and os.path.exists(path):
            path = os.path.abspath(path)
            if os.path.isdir(path):
                file = os.path.join(path, os.path.basename(default_file_name))
                dir = path
            elif os.path.isfile(path):
                file = path
                dir = os.path.dirname(path)
        return (dir, file)

    def indent(self, modify = 0):
        if modify:
            self.indent_level += modify
            if self.indent_level < 0:
                raise Exception("Indent level can't drop below zero. Current level is %i." % (self.indent_level))
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
        call = ast.Call(to_call, [name], None, None, None)
        return self.compile_node(call)

    def compile(self):
        input_f = open(self.input_file_path, 'r')
        python_code = input_f.read(self.max_file_size)
        file_ast = ast.parse(python_code)
        print_node(file_ast)
        self.compile_Module(file_ast)
        if self.is_main_compiler:
            require_stmt = 'typeof require !== "undefined" && require("./python")'
            import_stmt = self.import_me()
            compiled = "%s;\n\n%s;\n\n%s;" % (require_stmt, ";\n\n".join(self.modules), import_stmt)
            output_f = open(self.output_file_path, 'w+')
            output_f.write(compiled)

    def compile_node(self, node, *args):
        if isinstance(node, list):
            f = self.compile_node_list
        else:
            class_name = node.__class__.__name__
            f = getattr(self, "compile_%s" % class_name)
            if not f:
                raise Exception("No compiler for AST node %s" % class_name)
        return f(node, *args)

    def compile_node_list(self, nodes, joiner = ";\n", trailing = ";"):
        compiled = [self.compile_node(n) for n in nodes]
        result = joiner.join(filter(lambda x: x, compiled))
        if trailing:
            result += trailing
        return result

    def compile_Module(self, node):
        module_name = ast.Str(self.module_name)
        args = ast.arguments([ast.arg(self.local_module_name.id, None)], None, None, None, None, None, None, None)
        func = ast.FunctionDef(name = '', args = args, body = node.body, decorator_list = [], returns = None)
        to_call = JSCode("__python__.register_module")
        call = ast.Call(to_call, [module_name, func], None, None, None)
        result = self.compile_node(call)
        self.main_compiler.modules.append(result)

    def compile_Import(self, node):
        names = node.names
        results = []
        for alias in names:
            name = alias.name
            file_name = "%s.py" % os.path.join(self.input_directory_path, name)
            compiler = Compiler(file_name, self.main_compiler)
            import_call = compiler.import_me()
            asname = ast.Name(alias.asname or name, ast.Store())
            assign = ast.Assign([asname], JSCode(import_call))
            results.append(assign)
        return self.compile_node_list(results, ", ", "")

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

    def compile_Call(self, node):
        func = self.compile_node(node.func)
        args = self.compile_node_list(node.args, ", ", "")
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
        attrstring = ast.Str(node.attr)
        if isinstance(ctx, ast.Store):
            func = JSCode('%s.__setattribute__' % value)
            args = [attrstring, assign]
        elif isinstance(ctx, ast.Load):
            func = JSCode('%s.__getattribute__' % value)
            args = [attrstring]
        else:
            raise Exception("Can't compile attribute with context of type %s" % ctx.__class__.__name__)
        call = ast.Call(func, args, None, None, None)
        return self.compile_node(call)

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
        return "__python__.__eq__"

    def compile_NotEq(self, node):
        return "__python__.__not_eq__"

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
    def compile_Name(self, node):
        id = node.id
        if id in self.javascript_reserved_words:
            id = "$%s" % id

        ctx = node.ctx
        if isinstance(ctx, ast.Store):
            active_ctx = self.context_stack[-1]
            if active_ctx.is_global(node):
                active_ctx = self.context_stack[0]
            active_ctx.set(node)
        else:
            active_ctx = self.context_stack.find(node) or (self.context_stack and self.context_stack[0])

        is_local_module_name = node is self.local_module_name
        if not is_local_module_name and active_ctx and active_ctx.is_module_context():
            local_module_name = self.compile_node(self.local_module_name)
            return "%s.%s" % (local_module_name, id)
        elif active_ctx and active_ctx.is_class_context():
            return "%s.%s.%s" % (active_ctx.class_name, "prototype", id)
        else:
            return id

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
        body = self.compile_node_list(node.body, ";\n%s" % indent1, ";")

        if not ctx.is_module_context() and not ctx.is_class_context():
            declare_locals = ", ".join(ctx.locals)
            if declare_locals:
                declare_locals = "%svar %s;\n" % (indent1, declare_locals)
        else:
            declare_locals = ""

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
