import ast, inspect, re

class Builtins:
    re_dedent1 = re.compile(r"^(    |\t)", re.MULTILINE)

    def __init__(self):
        self.usedict = {}
        self.module_text = ""

    def use(self, name):
        try:
            used = self.usedict[name]
        except KeyError:
            used = False

        if not used:
            self.usedict[name] = True
            try:
                method = self.__getattribute__(name)
            except AttributeError:
                return

            method_text = inspect.getsource(method)
            # Dedent by one
            method_text = self.re_dedent1.sub('', method_text)

            # This makes sure that we use any other builtins that this builtin method requires.
            nodes = ast.parse(method_text)
            for node in ast.walk(nodes):
                if isinstance(node, ast.Name):
                    self.use(node.id)

            self.module_text += method_text

    def _clone(o):
        if Object.create:
            return Object.create(o)
        else:
            f = lambda: None
            f.prototype = o
            return jseval("new f()")

    def _each(o, fn):
        jseval("for (var prop in o) { " \
               "if (o.hasOwnProperty(prop)) { " \
               "fn(prop, o[prop]); "
               "} "
               "}")

    def eq(a, b):
        pass

    def isinstance(item, cls):
        if item and jseval("item instanceof cls") and jseval("typeof item") == cls.name:
            return True
        else:
            return False

    def instantiate_class(self, cls):
        if not isinstance(self, cls):
            self = _clone(cls.prototype)

        def each_method(prop, fn):
            if isinstance(fn, Function):
                self[prop] = fn.bind(self)

        _each(self, each_method)

        return self

    class list(Array):
        pass
