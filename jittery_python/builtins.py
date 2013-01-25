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
        {"Object": "Function"}
        if Object.create:
            return Object.create(o)
        else:
            def f(): pass
            f.prototype = o
            return jseval("new f()")

    def _each(o, fn, own = True):
        jseval("for (var prop in o) { " \
               "if (!own || o.hasOwnProperty(prop)) { " \
               "fn(prop, o[prop], {}); "
               "} "
               "}")

    def _keys(o):
        {"Object": "Function", "keys": "Array"}
        if Object.keys:
            return Object.keys(o)
        else:
            keys = []
            _each(o, lambda k, v: keys.push(k))
            return keys

    def _typeof(o, t):
        {'toString': 'Function', 't': 'String'}
        toString = Object.prototype.toString
        t = toString.call(o)
        t = t.substring(8, t.length - 1)
        return t.toLowerCase()

    def _null(o):
        return jseval("o == null")

    # Internal implementation functions
    def __eq__(a, b):
        if not __eq__.warn:
            __eq__.warn = True
            print("Warning: == and != are not yet properly implemented. Currently an `is` or `is not` operation is used instead.")
        return a is b

    def __in__(ls, check):
        {'a': 'Array'}
        if _typeof(ls) is Array:
            a = ls
            if a.indexOf(check) >= 0:
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

            {'ret': 'Array'}
            ret = []
            while idx >= 0 and idx <= endidx:
                ret.push(ls[idx])
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

        # This will go away when static methods work.
        jseval("return __ModuleList__()")

    def __registermodule__(name, fn):
        __ModuleList__.__register__(name, fn)

    def __import__(name):
        return __ModuleList__.__import__(name)

    # Public functions
    def str(o):
        {'so': 'Object'}
        if _null(o):
            return "None"
        elif o is True:
            return "True"
        elif o is False:
            return "False"
        elif _typeof(o.__str__) is "function":
            return o.__str__()
        elif _typeof(o.toString) is "function":
            so = o
            return so.toString()
        else:
            return "" + o

    def len(ls):
        return ls.length

    def bool(x): return not not x

    def _in_browser():
        return jseval("typeof window") is not "undefined"

    def print(*objects, sep=' ', end='', file=None, flush=False):
        {'_console': 'Object'}
        _console = console
        string = [str(o) for o in objects].join(sep) + end
        _console.log(string)

    # Class stuff
    def isinstance(item, cls):
        return jseval("item instanceof cls")

    def __class_extend__(child, parent):
        if child is not parent:
            {'sup': 'Function'}
            sup = _super
            child.prototype = _clone(parent.prototype)
            child.prototype.constructor = child
            child.prototype.super = sup.bind(null, parent)
        else: # child and parent are both `object`
            child.prototype.super = _super

    def __class_instantiate__(cls, self, args, child_self = None):
        if not isinstance(self, cls):
            self = _clone(cls.prototype)

        in_super = bool(child_self)
        context = child_self or self
        special_fns = ["constructor"]

        def each_method(prop, fn):
            {'fn': 'Function'}
            if isinstance(fn, Function) and prop not in special_fns:
                if in_super:
                    if prop is "$super": return None
                    def tmp(*args: 'Array', **kwargs):
                        {'sup': 'Function'}
                        old_sup = context.super
                        __super__ = context.__super__
                        sup = cls.prototype.super
                        context.super = sup.bind(null, context)
                        context.__super__ = None

                        args.unshift(context)
                        args.push(kwargs)
                        result = fn.apply(null, args)

                        context.super = old_sup
                        context.__super__ = __super__
                        return result

                    self[prop] = tmp
                else:
                    self[prop] = fn.bind(null, context)

        _each(cls.prototype, each_method, False)

        if _typeof(self.__init__) is "function" and args is not None:
            _args = args[:]
            self.__init__(*_args)

        return self

    def _super(parent, self):
        if not self.__super__:
            self.__super__ = __class_instantiate__(parent, None, None, self)
        return self.__super__

    class object:
        def __init__(self):
            pass

    class slice:
        def __init__(self, start, stop, step):
            self.start = start
            self.stop = stop
            self.step = step

    class _static_array:
        def __init__(self, iterable = jseval("[]")):
            {'array': 'Array'}
            if _typeof(iterable) is "array":
                array = iterable
            elif isinstance(iterable, list):
                array = []
                for x in iterable:
                    array.push(x)
            elif isinstance(iterable, dict):
                self.__init__(iterable.keys())
                return
            elif _typeof(iterable) is "object" and not isinstance(iterable, object):
                array = _keys(iterable)
            else:
                raise TypeError("%s is not iterable" % (iterable and iterable.__class__.__name__))
            self.__storage = array

        def __getindex__(self, idx):
            {'storage': 'Array'}
            storage = self.__storage
            return storage[idx]

        def __str__(self):
            result = ""
            sep = ", "
            for x in self.__storage:
                if result:
                    result += sep
                result += str(x)
            return result

    class list(_static_array):
        def append(self, x):
            {'storage': 'Array'}
            storage = self.__storage
            storage.push(x)

        def __str__(self):
            return "[" + super().__str__() + "]"

    class tuple(_static_array):
        def __str__(self):
            return "(" + super().__str__() + ")"

    class dict: pass
