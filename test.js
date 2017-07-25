var JITTERY = (function () {
"use strict";

var JITTERY = {};

var modules = {};

JITTERY.register_module = function (fname, modname, fn) {
    if (modname in modules) {
        throw new Error('Can\'t specify module ' + modname + ' more than once');
    }
    modules[modname] = {
        filename: fname,
        module_name: modname,
        load: fn,
        module: null
    };
    if (modname === '__main__') {
        JITTERY.__import__(modname, null, null, [], 0);
    }
};

JITTERY.__import__ = function (name, globals, locals, fromlist, level) {
    console.assert(level === 0);  // TODO implement local imports
    console.assert(globals === null);  // TODO figure out what this does
    console.assert(locals === null);  // TODO figure out what this does

    var module = modules[name];
    if (!module.module) {
        module.module = module.load.__call__([{}], null);
    }
    return module.module;
}

JITTERY.__call__ = function __call__(c, args, kwargs) {
    if ('__call__'  in c) {
        return c.__call__.call(this, args, kwargs)
    } else {
        if (kwargs) {
            args = args.concat([kwargs]);
        }
        return c.apply(this, args);
    }
};

JITTERY.allkeys = function allkeys(obj) {
    var keys = [];
    for (var k in obj) {
        keys.push(k);
    }
    return keys;
};

JITTERY.bind = function (fn, self) {
    return function(args, kwargs) {
        return fn([self].concat(args), kwargs);
    };
}

JITTERY.bindall = function (self) {
    for (var k in self) {
        if (typeof self[k] === 'function' && k !== '__class__') {
            self[k] = JITTERY.bind(self[k], self);
        }
    }
};

return JITTERY;

})();

JITTERY.__call__.call(JITTERY, JITTERY.register_module, ["/home/ubuntu/client.py/runtime/builtins.py", "builtins", (function () {
    "use strict";
    function $fn($args) {
        "use strict";
        var iter, __import__, next, len, Exception, hasattr, __module__, __name__, range, isinstance, $module, Iterator, print, IndexableIterator, StopIteration, __file__;
        $module = $args[0];
        $module.__module__ = $module;
        $module.__name__ = "builtins";
        $module.__file__ = "/home/ubuntu/client.py/runtime/builtins.py";
        "\
bare module\
";
        $module.__import__ = JITTERY.__import__;
        $module.Exception = (function () {
            "use strict";
            var $Exception;
            function $fn2($args1) {
                "use strict";
                var $self;
                $self = Object.create($Exception.prototype);
                $self.__class__ = $Exception;
                JITTERY.bindall($self);
                $self.__init__ && $self.__init__.apply(null, arguments);
                return $self;
            };
            $Exception = $fn2;
            $fn2.__call__ = $fn2;
            $Exception.__name__ = "Exception";
            $Exception.prototype = JITTERY.__call__.call(($module.Object || Object), ($module.Object || Object).create, [($module.Error || Error).prototype], null);
            function $fn3($args1) {
                "use strict";
                var self, msg;
                self = $args1[0];
                msg = $args1[1];
                self.name = self.__class__.__name__;
                self.message = msg;
                self.stack = (new Error()).stack;
            };
            $Exception.prototype.__init__ = $fn3;
            $fn3.__call__ = $fn3;
            return $Exception;
        })();
        $module.StopIteration = (function () {
            "use strict";
            var $StopIteration;
            function $fn2($args1) {
                "use strict";
                var $self;
                $self = Object.create($StopIteration.prototype);
                $self.__class__ = $StopIteration;
                JITTERY.bindall($self);
                $self.__init__ && $self.__init__.apply(null, arguments);
                return $self;
            };
            $StopIteration = $fn2;
            $fn2.__call__ = $fn2;
            $StopIteration.__name__ = "StopIteration";
            $StopIteration.prototype = JITTERY.__call__.call(($module.Object || Object), ($module.Object || Object).create, [$module.Exception.prototype], null);
            return $StopIteration;
        })();
        $module.Iterator = (function () {
            "use strict";
            var $Iterator;
            function $fn2($args1) {
                "use strict";
                var $self;
                $self = Object.create($Iterator.prototype);
                $self.__class__ = $Iterator;
                JITTERY.bindall($self);
                $self.__init__ && $self.__init__.apply(null, arguments);
                return $self;
            };
            $Iterator = $fn2;
            $fn2.__call__ = $fn2;
            $Iterator.__name__ = "Iterator";
            function $fn3($args1) {
                "use strict";
                var self;
                self = $args1[0];
                return self;
            };
            $Iterator.prototype.__iter__ = $fn3;
            $fn3.__call__ = $fn3;
            return $Iterator;
        })();
        $module.IndexableIterator = (function () {
            "use strict";
            var $IndexableIterator;
            function $fn2($args1) {
                "use strict";
                var $self;
                $self = Object.create($IndexableIterator.prototype);
                $self.__class__ = $IndexableIterator;
                JITTERY.bindall($self);
                $self.__init__ && $self.__init__.apply(null, arguments);
                return $self;
            };
            $IndexableIterator = $fn2;
            $fn2.__call__ = $fn2;
            $IndexableIterator.__name__ = "IndexableIterator";
            $IndexableIterator.prototype = JITTERY.__call__.call(($module.Object || Object), ($module.Object || Object).create, [$module.Iterator.prototype], null);
            function $fn3($args1) {
                "use strict";
                var arr, self;
                self = $args1[0];
                arr = $args1[1];
                self.arr = arr;
                self.i = 0;
            };
            $IndexableIterator.prototype.__init__ = $fn3;
            $fn3.__call__ = $fn3;
            function $fn4($args1) {
                "use strict";
                var i, self, result;
                self = $args1[0];
                if ((($module.i || i) < JITTERY.__call__.call(null, ($module.len || len), [($module.arr || arr)], null))) {
                    result = ($module.arr || arr)[($module.i || i)];
                    i += 1;
                    return result;
                } else  {
                    throw JITTERY.__call__.call($module, $module.StopIteration, [], null);
                }
            };
            $IndexableIterator.prototype.__next__ = $fn4;
            $fn4.__call__ = $fn4;
            return $IndexableIterator;
        })();
        $module.range = (function () {
            "use strict";
            var $range;
            function $fn2($args1) {
                "use strict";
                var $self;
                $self = Object.create($range.prototype);
                $self.__class__ = $range;
                JITTERY.bindall($self);
                $self.__init__ && $self.__init__.apply(null, arguments);
                return $self;
            };
            $range = $fn2;
            $fn2.__call__ = $fn2;
            $range.__name__ = "range";
            $range.prototype = JITTERY.__call__.call(($module.Object || Object), ($module.Object || Object).create, [$module.Iterator.prototype], null);
            function $fn3($args1) {
                "use strict";
                var step, start, self, stop;
                self = $args1[0];
                start = $args1[1];
                stop = (((JITTERY.__call__.call(null, ($module.len || len), [$args1], null) > 2)) ? ($args1[2]) : (null));
                step = (((JITTERY.__call__.call(null, ($module.len || len), [$args1], null) > 3)) ? ($args1[3]) : (1));
                if ((stop === null)) {
                    [stop, start] = [start, 0];
                }
                self.start = start;
                self.stop = stop;
                self.step = step;
                self._val = self.start;
            };
            $range.prototype.__init__ = $fn3;
            $fn3.__call__ = $fn3;
            function $fn4($args1) {
                "use strict";
                var self, result;
                self = $args1[0];
                if ((self._val >= self.stop)) {
                    throw JITTERY.__call__.call($module, $module.StopIteration, [], null);
                }
                result = self._val;
                self._val += self.step;
                return result;
            };
            $range.prototype.__next__ = $fn4;
            $fn4.__call__ = $fn4;
            return $range;
        })();
        function $fn1($args1) {
            "use strict";
            var it;
            it = $args1[0];
            if ((it && it.__iter__)) {
                return JITTERY.__call__.call(it, it.__iter__, [], null);
            } else  {
                if (JITTERY.__call__.call(($module.Array || Array), ($module.Array || Array).isArray, [it], null)) {
                    return JITTERY.__call__.call($module, $module.IndexableIterator, [it], null);
                } else  {
                    return JITTERY.__call__.call($module, $module.IndexableIterator, [JITTERY.__call__.call(($module.Object || Object), ($module.Object || Object).keys, [it], null)], null);
                }
            }
        };
        $module.iter = $fn1;
        $fn1.__call__ = $fn1;
        function $fn2($args1) {
            "use strict";
            var it;
            it = $args1[0];
            return JITTERY.__call__.call(it, it.__next__, [], null);
        };
        $module.next = $fn2;
        $fn2.__call__ = $fn2;
        function $fn3($args1) {
            "use strict";
            var o, attr;
            o = $args1[0];
            attr = $args1[1];
            return attr in o;
        };
        $module.hasattr = $fn3;
        $fn3.__call__ = $fn3;
        function $fn4($args1) {
            "use strict";
            var l;
            l = $args1[0];
            if (JITTERY.__call__.call($module, $module.hasattr, [l, "length"], null)) {
                return l.length;
            } else  {
                return JITTERY.__call__.call(l, l.__len__, [], null);
            }
        };
        $module.len = $fn4;
        $fn4.__call__ = $fn4;
        function $fn5($args1) {
            "use strict";
            var objects;
            objects = JITTERY.__call__.call(($module.Array || Array).prototype.slice, ($module.Array || Array).prototype.slice.call, [$args1, 0], null);
            JITTERY.__call__.call(($module.console || console).log, ($module.console || console).log.apply, [($module.console || console), objects], null);
        };
        $module.print = $fn5;
        $fn5.__call__ = $fn5;
        function $fn6($args1) {
            "use strict";
            var $running, a, b, $iter, t_, $exc;
            a = $args1[0];
            b = $args1[1];
            if (JITTERY.__call__.call(($module.Array || Array), ($module.Array || Array).isArray, [b], null)) {
                $iter = JITTERY.__call__.call($module, $module.iter, [b], null);
                $running = true;
                while ($running) {
                    try {
                        t_ = JITTERY.__call__.call($module, $module.next, [$iter], null);
                        if (a instanceof t_) {
                            return true;
                        }
                    } catch ($exc) {
                        if (JITTERY.__call__.call(null, ($module.isinstance || isinstance), [$exc, $module.StopIteration], null)) {
                            $running = false;
                        } else  {
                            throw $exc;
                        }
                    };
                }
                return false;
            } else  {
                return a instanceof b;
            }
        };
        $module.isinstance = $fn6;
        $fn6.__call__ = $fn6;
        return $module;
    };
    $fn.__call__ = $fn;
    return $fn;
})()], null)
JITTERY.__call__.call(JITTERY, JITTERY.register_module, ["/home/ubuntu/client.py/test/__main__.py", "__main__", (function () {
    "use strict";
    function $fn($args) {
        "use strict";
        var builtins, __name__, $running, $module1, fn, $iter1, $iter, i, $running1, __module__, $import, $exc1, __file__, $exc;
        $module1 = $args[0];
        $import = JITTERY.__call__.call(JITTERY, JITTERY.__import__, ["builtins", null, null, ["*"], 0], null);
        $module1.builtins = $import;
        $module1.__module__ = $module1;
        $module1.__name__ = "__main__";
        $module1.__file__ = "/home/ubuntu/client.py/test/__main__.py";
        function $fn1($args1, kwargs) {
            "use strict";
            var kwargs, a, args, b;
            a = $args1[0];
            b = $args1[1];
            args = JITTERY.__call__.call(($module1.builtins.Array || ($module1.Array || Array)).prototype.slice, ($module1.builtins.Array || ($module1.Array || Array)).prototype.slice.call, [$args1, 2], null);
            kwargs = (kwargs || {});
            JITTERY.__call__.call(null, ($module1.builtins.print || ($module1.print || print)), ["a = ", a], null);
            JITTERY.__call__.call(null, ($module1.builtins.print || ($module1.print || print)), ["b = ", b], null);
            JITTERY.__call__.call(null, ($module1.builtins.print || ($module1.print || print)), ["*args = ", args], null);
            JITTERY.__call__.call(null, ($module1.builtins.print || ($module1.print || print)), ["**kwargs = ", kwargs], null);
        };
        $module1.fn = $fn1;
        $fn1.__call__ = $fn1;
        JITTERY.__call__.call($module1, $module1.fn, [1, 2, 3, 4, 5, 6], {"f": 1, "g": 2});
        $iter = JITTERY.__call__.call(null, ($module1.builtins.iter || ($module1.iter || iter)), [JITTERY.__call__.call(null, ($module1.builtins.range || ($module1.range || range)), [10], null)], null);
        $running = true;
        while ($running) {
            try {
                $module1.i = JITTERY.__call__.call(null, ($module1.builtins.next || ($module1.next || next)), [$iter], null);
                JITTERY.__call__.call(null, ($module1.builtins.print || ($module1.print || print)), [$module1.i], null);
            } catch ($exc) {
                if (JITTERY.__call__.call(null, ($module1.builtins.isinstance || ($module1.isinstance || isinstance)), [$exc, ($module1.builtins.StopIteration || ($module1.StopIteration || ($module1.builtins.StopIteration || ($module1.StopIteration || StopIteration))))], null)) {
                    $running = false;
                } else  {
                    throw $exc;
                }
            };
        }
        JITTERY.__call__.call(null, ($module1.builtins.print || ($module1.print || print)), ["range(2, 12, 2)"], null);
        $iter1 = JITTERY.__call__.call(null, ($module1.builtins.iter || ($module1.iter || iter)), [JITTERY.__call__.call(null, ($module1.builtins.range || ($module1.range || range)), [2, 12, 2], null)], null);
        $running1 = true;
        while ($running1) {
            try {
                $module1.i = JITTERY.__call__.call(null, ($module1.builtins.next || ($module1.next || next)), [$iter1], null);
                JITTERY.__call__.call(null, ($module1.builtins.print || ($module1.print || print)), [$module1.i], null);
            } catch ($exc1) {
                if (JITTERY.__call__.call(null, ($module1.builtins.isinstance || ($module1.isinstance || isinstance)), [$exc1, ($module1.builtins.StopIteration || ($module1.StopIteration || ($module1.builtins.StopIteration || ($module1.StopIteration || StopIteration))))], null)) {
                    $running1 = false;
                } else  {
                    throw $exc1;
                }
            };
        }
        return $module1;
    };
    $fn.__call__ = $fn;
    return $fn;
})()], null)
