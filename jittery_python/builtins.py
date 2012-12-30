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
        if name is "use" or name not in Builtins.__dict__:
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
                    if attr.startswith("__class_"):
                        self.use(attr)

            self.module_text += item_text

    # Utilities
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

    def _typeof(o, t):
        type = Object.prototype.toString.call(o)
        type = type.substring(8, type.length - 1).toLowerCase()
        return t is type

    def _null(o):
        return jseval("o == null")

    # Internal implementation functions
    def __eq__(a, b):
        print("Warning: == and != are not yet properly implemented. Currently an is or is not operation is used instead.")
        return a is b

    def __slice__(ls, lower, upper, step):
        if step is None or step is 1:
            if upper:
                return ls.slice(lower or 0, upper)
            elif lower:
                return ls.slice(lower)
            else:
                return ls.slice()
        else:
            idx = lower or 0
            length = len(ls)
            if upper is not None:
                endidx = upper
            else:
                endidx = length
            ret = []
            while idx < length or idx >= endidx:
                ret.push(ls[idx])
                idx += step
            return ret

    # Public functions
    def str(o):
        if not _null(o) and _typeof(o.toString) is "function":
            return o.toString()
        else:
            return "" + o

    def print(*objects, sep=' ', end='\n', file=None, flush=False):
        string = sep.join([str(o) for o in objects]) + end
        console.log(string)

    # Class stuff
    def isinstance(item, cls):
        if item and (jseval("item instanceof cls") or jseval("typeof item") == cls.name):
            return True
        else:
            return False

    def __class_extend__(child, parent):
        child.prototype = _clone(parent.prototype)
        child.prototype.constructor = child
        child.prototype.super = object.prototype.super.bind(null, parent)

    def __class_instantiate__(self, args, cls, child_self = None):
        if not isinstance(self, cls):
            self = _clone(cls.prototype)

        context = child_self or self
        def each_method(prop, fn):
            if isinstance(fn, Function):
                self[prop] = fn.bind(null, context)

        _each(cls.prototype, each_method)

        if _typeof(self.__init__, "function") and args is not None:
            args = [self] + args
            self.__init__(*args)

        return self

    class object:
        def super(parent, self):
            if not self.__super__:
                self.__super__ = __class_instantiate__(None, None, parent, self)
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
