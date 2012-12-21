(function (root) {

    var clone = Object.create || function (o) {
        function F() {}
        F.prototype = o;
        return new F();
    };

    var __python__ = root.__python__ = {};
    var modules = __python__.modules = {};
    var module_fns = {};

    __python__.register_module = function (name, fn) {
        module_fns[name] = fn;
    };

    __python__.floor_div = function (a, b) {
        return Math.floor(a / b);
    };

    __python__.eq = function (a, b) {
        console.warn("__python__.__eq__ is not yet properly implemented!")
        return a === b;
    };

    __python__.not_eq = function (a, b) {
        return !__python__.__eq__(a, b);
    };

    var getPrototype = Object.getPrototype || function (o) {
        return o.constructor.prototype;
    };

    var hasOwnOrInheritedProperty = function (o, attr) {
        if (o instanceof object) {
            if (o.hasOwnProperty(attr)) {
                return true;
            } else {
                return hasOwnOrInheritedProperty(getPrototype(o));
            }
        } else {
            return false;
        }
    };

    __python__.Class = function (name, cls) {
        cls.__name__ = name;
        cls.__class__ = cls;
        var fn = __init__.bind(null, cls);
        fn.__getattribute__ = __getattribute__.bind(null, cls);
        fn.__setattribute__ = __setattribute__.bind(null, cls);
        return cls;
    };

    __python__.__register_module__("__builtin__", function (builtin) {
        builtin.print = console.log.bind(console);

        builtin.__import__ = function (name) {
            if (!modules[name]) {
                var fn = module_fns[name];
                context = clone(__modules__.__builtin__ || root);
                context.__name__ = name;
                fn(context);
                modules[name] = context;
                return context;
            } else {
                return modules[name];
            }
        };

        var __getattribute__ = function (self, attr) {
            // Look for attr in self directly.
            if (attr in self) {
                return self[attr];
            }

            // Look for attr in __dict__.
            var dict = self.__getattribute__("__dict__")
            if (attr in dict) {
                return dict[attr];
            }

            // Look for attr in __class__.
            var cls = self.__getattribute__("__class__");
            try { return cls.__getattribute__(attr); }
            catch (e) {}

            // Look for attr in __bases__ (if available).
            var bases = self.__getattribute__("__bases__");
            if (bases) {
                for (var i = 0, len = bases.length; i < len; i++) {
                    var base = bases[i];
                    try { return base.__getattribute__(attr); }
                    catch (e) {}
                }
            }

            // attr not found.
            throw builtin.AttributeError("'" + self.constructor.name + "' object has no attribute '" + attr + "'");
        };

        var __setattribute__ = function (self, attr, value) {
            // If attr exists directly on self, set it directly on self as well.
            if (attr in self) {
                return self[attr] = value;
            }

            // Otherwise set it on __dict__.
            var dict = self.__getattribute__("__dict__");
            if (dict.__class__) {
                return dict.__setitem__(attr, value);
            } else {
                return dict[attr] = value;
            }
        };

        var set_up_getters_setters(obj, getters, setters) {
            if (getters) {
                obj.__getattribute__ = __getattribute__.bind(null, obj);
            }
            if (setters) {
                obj.__setattribute__ = __setattribute__.bind(null, obj);
            }
        };

        var type__init__ = function (name, bases, dict) {
            if (arguments.length === 1) {
                var obj = name;
                return obj.__class__;
            } else if (arguments.length === 3) {
                var cls = function () {
                    var self = {};
                    self.__class__ = cls;
                    if (builtin.dict) {
                        self.__dict__ = builtin.dict();
                    } else {
                        self.__dict__ = {};
                    }
                    var __dict__ = self.__dict__;

                    var $super;
                    self.__super__ = function () {
                        if (!$super) {
                            var blank_obj = clone(null);
                            $super = {
                                __dict__: blank_obj,
                                __bases__: cls.__bases__
                            };
                            set_up_getters_setters($super, true, true);
                        }
                        return $super;
                    };

                    for (var prop in cls) {
                        var fn = cls[prop];
                        if (hasOwnOrInheritedProperty(cls, prop) && typeof fn === "function") {
                            var bound = fn.bind(null, self);
                            if (__dict__.__class__) {
                                __dict__.__setitem__(prop, bound);
                            } else {
                                __dict__[prop] = bound;
                            }
                        }
                    }

                    if (typeof self.__init__ === "function") {
                        var result = self.__init__.apply(null, arguments);
                        if (cls === builtin.type) {
                            return result;
                        } else {
                            throw new TypeError("__init__() should return None, not '" + result.__class__.__name__ + "'");
                        }
                    }

                    return self;
                };

                cls.__qualname__ = cls.__name__ = name;
                cls.__class__ = builtin.type;
                cls.__bases__ = bases;
                cls.__dict__ = dict;
                set_up_getters_setters(cls, true, true);

                return cls;
            } else {
                throw new TypeError("type() takes 1 or 3 arguments");
            }
        };

        builtin.object = type__init__("object", [], {});

        builtin.type = type__init__('type', [builtin.object], {
            __init__: type__init__,
            __getattribute__: __getattribute__,
            __setattribute__: __setattribute__
        });
        builtin.type.__class__ = builtin.type
        builtin.object.__class__ = builtin.type

        builtin.dict = builtin.type('dict', [builtin.object], {
            __init__: function (obj) {
                self._keys = [];
                self._values = [];
                if (obj) {
                    for (var prop in obj) {
                        if (obj.hasOwnProperty(prop)) {
                            self._keys.push(prop);
                            self._values.push(obj[prop]);
                        }
                    }
                }
            },

            _getkey = function (self, key) {
                if (key != null && typeof key === "object") {
                    if (key.__hash__) {
                        return key.__hash__();
                    } else {
                        throw new TypeError("unhashable type: " + key.__class__.__name__);
                    }
                } else {
                    return key;
                }
            },

            __getitem__ = function (self, key) {
                key = self.__getkey__(key);
                var index = self._keys.indexOf(key);
                return self._values[index];
            },

            __setitem__ = function (self, key, value) {
                key = self._getkey(key);
                var index = this.keys.indexOf(key);
                if (index >= 0) {
                    self._values[index] = value;
                } else {
                    self._keys.push(key);
                    self._values.push(value);
                }
                return value;
            }
        });
        builtin.type.__dict__ = builtin.dict(builtin.type.__dict__);
        builtin.object.__dict__ = builtin.dict(builtin.object.__dict__);
        builtin.dict.__dict__ = builtin.dict(builtin.dict.__dict__);

        builtin.tuple = builtin.type('tuple', [builtin.object], builtin.dict({
            __init__: function (self, iterable) {
                if (iterable) {
                    self._list = iterable.slice();
                } else {
                    self._list = [];
                }
            },

            __setitem__: function (self, idx, value) {
                self._list[idx] = value;
            },

            __getitem__: function (self, idx) {
                if (idx < self._list.length) {
                    return self._list[idx];
                } else {
                    throw IndexError("list index out of range");
                }
            }
        }));
        builtin.type.__bases__ = builtin.tuple(builtin.type.__bases__);
        builtin.object.__bases__ = builtin.tuple(builtin.object.__bases__);
        builtin.dict.__bases__ = builtin.tuple(builtin.dict.__bases__);
        builtin.tuple.__bases__ = builtin.tuple(builtin.tuple.__bases__);

        builtin.list = builtin.type('list', builtin.tuple([builtin.object]), builtin.dict({
            __init__: builtin.tuple.__getattribute__('__init__'),
            __setitem__: builtin.tuple.__getattribute__('__setitem__'),
            __getitem__: builtin.tuple.__getattribute__('__getitem__'),

            append: function (self, item) {
                self._list.push(item);
            },

            pop: function (self) {
                self._list.pop();
            }
        }));
    });
    __python__.__import_module__("__builtin__");

})(typeof global === "undefined" ? window : global);
