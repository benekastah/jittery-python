import ast, inspect, re

# A few definitions to mimic the javascript environment.
# If these are missing we get an error.
class Array: pass
class Error: pass

class Builtins:
    re_dedent1 = re.compile(r"^(    |\t)", re.MULTILINE)

    def __init__(self):
        self.usedict = {}
        self.module_text = ""

    def use(self, name):
        if name is "use":
            return

        try:
            used = self.usedict[name]
        except KeyError:
            used = False

        if not used:
            self.usedict[name] = True
            try:
                item = self.__getattribute__(name)
            except AttributeError:
                return

            item_text = inspect.getsource(item)
            # Dedent by one
            item_text = self.re_dedent1.sub('', item_text)

            # This makes sure that we use any other builtins that this builtin item requires.
            nodes = ast.parse(item_text)
            for node in ast.walk(nodes):
                if isinstance(node, ast.Name):
                    self.use(node.id)

            if isinstance(item, type):
                for attr in dir(self):
                    if attr.startswith("_class_"):
                        self.use(attr)

            self.module_text += item_text

    class Exception(Error): pass

    def _clone(o):
        if Object.create:
            return Object.create(o)
        else:
            def f(): pass
            f.prototype = o
            return jseval("new f()")

    def _each(o, fn):
        jseval("for (var prop in o) { " \
               "if (o.hasOwnProperty(prop)) { " \
               "fn(prop, o[prop]); "
               "} "
               "}")

    def __eq__(a, b):
        pass

    def isinstance(item, cls):
        if item and jseval("item instanceof cls") and jseval("typeof item") == cls.name:
            return True
        else:
            return False

    def _class_extend(child, parent):
        child.prototype = _clone(parent.prototype)
        child.prototype.constructor = child
        child.prototype.super = object.prototype.super.bind(null, parent)

    def _class_instantiate(self, cls, child_self = None):
        if not isinstance(self, cls):
            self = _clone(cls.prototype)

        context = child_self or self
        def each_method(prop, fn):
            if isinstance(fn, Function):
                self[prop] = fn.bind(null, context)

        _each(cls.prototype, each_method)

        return self

    class object:
        def super(parent, self):
            if not self.__super__:
                self.__super__ = _class_instantiate(None, parent, self)
            return self.__super__

    class ModifyError(Exception): pass

    class tuple(Array):
        def __init__(self, iterable):
            sup = super()
            for item in iterable:
                len = sup.push(item)
                index = len - 1
                self.__defineSetter__(index, self._modify_err)

        def _modify_err(self):
            raise ModifyError()

        push = None
        pop = None
        shift = None
        unshift = None
