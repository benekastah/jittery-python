import ast, inspect, re

# A few definitions to mimic the javascript environment.
# If these are missing we get an error.
class Array: pass
class Error: pass
def jseval(*a): pass

class Builtins:
    re_dedent1 = re.compile(r"^(    |\t)", re.MULTILINE)
    re_star = re.compile(r"\*")
    always_available = ["__import__", "__slice__", "__getindex__", "__eq__", "__in__",]

    def __init__(self):
        self.usedict = {}
        self.using = []
        self.module_text = ""

    def use(self, name):
        if name in ("use", "__init__") or name not in Builtins.__dict__:
            return

        try:
            used = self.usedict[name]
        except KeyError:
            used = False

        if not used and name not in self.using:
            self.using.append(name)
            self.usedict[name] = True

            # Stuff we want to have unconditionally (for now).
            for item in self.always_available:
                self.use(item)

            try:
                item = self.__getattribute__(name)
            except AttributeError:
                return

            item_text = inspect.getsource(item)
            # Dedent by one
            item_text = self.re_dedent1.sub('', item_text)

            # If this is a class, include everything that starts with __class_.
            if isinstance(item, type):
                self.use("object")
                for attr in dir(self):
                    if attr.startswith("__class_"):
                        self.use(attr)

            # This makes sure that we use any other builtins that this builtin item requires.
            nodes = ast.parse(item_text)
            for node in ast.walk(nodes):
                if isinstance(node, ast.Name):
                    self.use(node.id)
                elif isinstance(node, ast.Eq) or isinstance(node, ast.NotEq):
                    self.use("__eq__")

            self.module_text += item_text
            self.using.pop()

    # Utilities
    class Exception(Error): pass

    def _clone(o):
        if Object.create:
            return jseval("Object.create(o)")
        else:
            def f(): pass
            f.prototype = o
            return jseval("new f()")

    def _each(o, fn):
        jseval("for (var prop in o) { " \
               "if (o.hasOwnProperty(prop)) { " \
               "fn(prop, o[prop], {}); "
               "} "
               "}")

    def _keys(o):
        if Object.keys:
            return jseval("Object.keys(o)")
        else:
            keys = jseval("[]")
            _each(o, lambda k, v: jseval("keys.push(k)"))
            return keys

    def _typeof(o, t):
        type = jseval("Object.prototype.toString.call(o)")
        type = type.substring(8, type.length - 1).toLowerCase()
        return type

    def _null(o):
        return jseval("o == null")

    # Internal implementation functions
    def __eq__(a, b):
        print("Warning: == and != are not yet properly implemented. Currently an is or is not operation is used instead.")
        return a is b

    def __in__(check, ls):
        if jseval("ls.indexOf(check) >= 0"):
            return True

        for item in ls:
            if item == check:
                return True

        return False

    def __getindex__(ls, idx):
        if _typeof(idx) is "number":
            if idx < 0:
                idx += len(ls)
        return idx

    def __slice__(ls, lower, upper, step = 1):
        if lower < 0:
            lower += len(ls)
        if upper < 0:
            upper += len(ls)

        if _typeof(ls) is "array" and step is 1:
            if upper:
                return ls.slice(lower or 0, upper)
            elif lower:
                return ls.slice(lower)
            else:
                return ls.slice()
        else:
            idx = lower or 0
            if _typeof(upper) is "number":
                endidx = upper
            else:
                endidx = len(ls)
            endidx -= 1

            ret = []
            while idx >= 0 and idx <= endidx:
                jseval("ret.push(ls[idx])")
                idx += step
            return ret

    class __ModuleList__:
        _module_fns = {}
        _included_modules = {}

        def __register__(self, name, fn):
            self._module_fns[name] = fn

        def __import__(self, name):
            m = self._included_modules[name]
            if not m:
                fn = self._module_fns[name]
                m = {}
                m.__name__ = name
                fn(m)
                self._included_modules[name] = m
            return m

        jseval("return __ModuleList__()")

    def __registermodule__(name, fn):
        __ModuleList__.__register__(name, fn)

    def __import__(name):
        return __ModuleList__.__import__(name)

    # Public functions
    def str(o):
        if not _null(o) and _typeof(o.toString) is "function":
            return jseval("o.toString()")
        else:
            return "" + o

    def len(ls):
        return ls.length

    def bool(x): return not not x

    def print(*objects, sep=' ', end='\n', file=None, flush=False):
        string = [str(o) for o in objects].join(sep) + end
        jseval("console.log(string)")

    # Class stuff
    def isinstance(item, cls):
        if item and (jseval("item instanceof cls") or jseval("typeof item") == cls.name):
            return True
        else:
            return False

    def __class_extend__(child, parent):
        if child is not parent:
            child.prototype = _clone(parent.prototype)
            child.prototype.constructor = child
            child.prototype.super = jseval("_super.bind(null, parent)")
        else: # child and parent are both `object`
            child.prototype.super = _super

    def __class_instantiate__(cls, self, args, child_self = None):
        if not isinstance(self, cls):
            self = _clone(cls.prototype)

        in_super = bool(child_self)
        context = child_self or self
        special_fns = ["constructor"]

        def each_method(prop, fn):
            if isinstance(fn, Function) and prop not in special_fns:
                if in_super:
                    if prop is "$super": return None
                    def tmp(*args):
                        old_sup = context.super
                        __super__ = context.__super__
                        sup = cls.prototype.super
                        context.super = jseval("sup.bind(null, context)")
                        context.__super__ = None

                        result = jseval("_fn.apply(null, arguments)")

                        context.super = old_sup
                        context.__super__ = __super__
                        return result

                    self[prop] = tmp
                else:
                    self[prop] = jseval("fn.bind(null, context)")

        _each(cls.prototype, each_method)

        if _typeof(self.__init__) is "function" and args is not None:
            args = jseval("Array.prototype.slice.call(args)")
            jseval("args.unshift(self)")
            self.__init__(*args)

        return self

    def _super(parent, self):
        if not self.__super__:
            self.__super__ = __class_instantiate__(parent, None, None, self)
        return self.__super__

    class object:
        def __init__(self):
            # self.super_stack = []
            pass

    class slice:
        def __init__(self, start, stop, step):
            self.start = start
            self.stop = stop
            self.step = step

    class _static_array:
        def __init__(self, iterable):
            if _typeof(iterable) is "array":
                array = iterable
            elif isinstance(iterable, list):
                array = jseval("[]")
                for x in iterable:
                    jseval("array.push(x)")
            elif isinstance(iterable, dict):
                self.__init__(iterable.keys())
                return
            elif _typeof(iterable) is "object" and not isinstance(iterable, object):
                array = _keys(iterable)
            self.__storage = array

        def __getindex__(self, idx):
            return jseval("self.__storage[idx]")

    class list(_static_array):
        def __init__(self, iterable = jseval("[]")):
            if isinstance(iterable, object) or _typeof(iterable) is "array":
                super().__init__(iterable)
            elif _typeof(iterable) is "object":
                super().__init__(_keys(iterable))
            else:
                raise TypeError("%s is not iterable" % (iterable and iterable.__class__.__name__))

    class tuple(_static_array):
        def __init__(self, iterable):
            sup = super()
            for item in iterable:
                len = jseval("sup.push(item)")
                index = len - 1
                self.__defineSetter__(index, self._modify_err)

        def _modify_err(self):
            raise ModifyError()

        push = None
        pop = None
        shift = None
        unshift = None
