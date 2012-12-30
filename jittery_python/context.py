import ast

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

    def get_vars(self, should_get_vars = None):
        from jittery_python.compiler import JSCode
        if should_get_vars or (should_get_vars != False and not self.is_module_context() and not self.is_class_context()):
            if self.locals:
                return JSCode("var %s" % ', '.join(self.locals))
        return JSCode("")

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
        ctx = name.ctx
        if isinstance(ctx, ast.Store):
            context = self[-1]
        else:
            context = None
            for c in reversed(self):
                if c.get(id):
                    context = c
                    break
            if not context:
                context = self[0]
        if context.is_global(name):
            return self[0]
        else:
            return context
