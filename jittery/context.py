import ast
from jittery.utils import print_node

class Context:
    def __init__(self, stack, class_name = None):
        self.stack = stack
        self.class_name = class_name

        self.globals = []
        self.arguments = []
        self.locals = []
        self.types = {}

        self.is_module_context = False
        self.is_class_context = False
        self.exports = []

        if not self.stack:
            self.is_module_context = True

        if class_name:
            self.is_class_context = True

    @staticmethod
    def _get_key_id(key):
        if isinstance(key, str):
            return key
        elif isinstance(key, ast.Name):
            return key.id
        elif isinstance(key, ast.Str):
            return key.s
        else:
            raise Exception("Invalid key: %s" % str(key))

    def _key_is_in(self, key, ls):
        id = self._get_key_id(key)
        return id in ls

    def is_local(self, key):
        return self._key_is_in(key, self.locals) or self.is_argument(key)

    def is_argument(self, key):
        return self._key_is_in(key, self.arguments)

    def is_global(self, key):
        return self._key_is_in(key, self.globals)

    def is_export(self, key):
        return self._key_is_in(key, self.exports)

    def _set(self, key, include = True, ls = None):
        if ls is None:
            ls = self.locals

        if ls is self.locals:
            other_ls = self.exports if self.is_module_context or self.is_class_context else self.arguments
        else:
            other_ls = self.locals

        id = self._get_key_id(key)
        already_in_ls = id in ls
        already_in_other = id in other_ls

        if include and (self.is_module_context or id not in self.globals) and not already_in_other and not already_in_ls:
            ls.append(id)
        elif not include and already_in_ls:
            index = ls.index(id)
            del ls[index]

    def get_vars(self, should_get_vars = True):
        from jittery.compiler import JSCode
        if should_get_vars:
            if self.locals:
                return JSCode("var %s" % ', '.join(self.locals))
        return JSCode("")

    def set_local(self, key):
        self._set(key, ls = self.locals)

    def set_global(self, key):
        id = self._get_key_id(key)
        if id in self.locals:
            self._set(id, False)
            print("SyntaxWarning: name '%s' is assigned to before global declaration" % id)

        self.globals.append(id)

    def set_argument(self, arg):
        self._set(arg, ls = self.arguments)

    def set_export(self, exp):
        self._set(exp, ls = self.exports)

    def type(self, item, _type = None):
        id = self._get_key_id(item)
        if _type:
            self.types[id] = self._get_key_id(_type)
        else:
            try:
                return self.types[id]
            except KeyError:
                pass


class ContextStack(list):
    def new(self, class_name = None):
        ctx = Context(self, class_name)
        self.append(ctx)
        return ctx

    @staticmethod
    def _get_key_id(item):
        if isinstance(item, ast.Attribute):
            return ContextStack._get_key_id(item.value)
        else:
            try:
                return Context._get_key_id(item)
            except:
                pass

    def find(self, name):
        if not self:
            return None

        id = self._get_key_id(name)
        if not id:
            return None

        ctx = name.ctx
        last_context = self[-1]
        if isinstance(ctx, ast.Store):
            context = last_context
        else:
            context = None
            for c in reversed(self):
                if c.is_local(id) or c.is_export(id):
                    if c.is_class_context and c is not last_context:
                        continue
                    context = c
                    break
            if not context:
                context = self[0]
        if context.is_global(id):
            return self[0]
        else:
            return context

    def find_type(self, item):
        if isinstance(item, ast.Attribute):
            return None
        context = self.find(item)
        if context:
            return context.type(item)
