(function () {

var _each, isinstance, _clone, _typeof, __class_instantiate__, _super, __class_extend__, object, __ModuleList__, __registermodule__, Exception, ModifyError, tuple, _null, str, print, __slice__;
_each = function (o, fn) {
  for (var prop in o) { if (o.hasOwnProperty(prop)) { fn(prop, o[prop]); } };
};
isinstance = function (item, cls) {
  if (item && item instanceof cls || __eq__(typeof item, cls.name)) {
    return true;
  } else {
    return false;
  };
};
_clone = function (o) {
  var f;
  if (Object.create) {
    return Object.create(o);
  } else {
    f = function () {
      ;
    };
    f.prototype = o;
    return new f();
  };
};
_typeof = function (o, t) {
  var type;
  type = Object.prototype.toString.call(o);
  type = type.substring(8, type.length - 1).toLowerCase();
  return t === type;
};
__class_instantiate__ = function (self, args, cls, child_self) {
  var context, each_method;
  if (!isinstance(self, cls)) {
    self = _clone(cls.prototype);
  };
  context = child_self || self;
  each_method = function (prop, fn) {
    if (isinstance(fn, Function)) {
      self[prop] = fn.bind(null, context);
    };
  };
  _each(cls.prototype, each_method);
  if (_typeof(self.__init__, "function") && args !== null) {
    args = [self] + args;
    self.__init__();
  };
  return self;
};
_super = function (parent, self) {
  if (!self.__super__) {
    self.__super__ = __class_instantiate__(null, null, parent, self);
    return self.__super__;
  };
};
__class_extend__ = function (child, parent) {
  if (child !== parent) {
    child.prototype = _clone(parent.prototype);
    child.prototype.constructor = child;
    child.prototype.super = _super.bind(null, parent);
  } else {
    child.prototype.super = _super;
  };
};
object = function () {
  __class_extend__(object, object);
  function object() {
    return __class_instantiate__(this, arguments);
  };
  object.prototype.__init__ = function (self) {
    ;
  };
  return object;
}();
__ModuleList__ = function () {
  __class_extend__(__ModuleList__, object);
  function __ModuleList__() {
    return __class_instantiate__(this, arguments);
  };
  __ModuleList__.prototype._module_fns = {};
  __ModuleList__.prototype._included_modules = {};
  __ModuleList__.prototype.__register__ = function (self, name, fn) {
    self._module_fns[name] = fn;
  };
  __ModuleList__.prototype.__import__ = function (self, name) {
    var m, fn;
    m = self._included_modules[name];
    if (!m) {
      fn = self._module_fns[name];
      m = {};
      m.__name__ = name;
      fn(m);
      self._included_modules[name] = m;
    };
    return m;
  };
  try {
    __ModuleList__ = __ModuleList__();
  } catch (__err_64320__) {
    ;
  };
  return __ModuleList__;
}();
__registermodule__ = function (name, fn) {
  __ModuleList__.__register__(name, fn);
};
Exception = function () {
  __class_extend__(Exception, Error);
  function Exception() {
    return __class_instantiate__(this, arguments);
  };
  return Exception;
}();
ModifyError = function () {
  __class_extend__(ModifyError, Exception);
  function ModifyError() {
    return __class_instantiate__(this, arguments);
  };
  return ModifyError;
}();
tuple = function () {
  __class_extend__(tuple, Array);
  function tuple() {
    return __class_instantiate__(this, arguments);
  };
  tuple.prototype.__init__ = function (self, iterable) {
    var __self__, sup, __i_68842__, __len_7466__, __iter_29213__, item, len, index;
    __self__ = arguments[0];
    sup = __self__.$super();
    for (__i_68842__ = 0, __iter_29213__ = iterable, __len_7466__ = __iter_29213__.length; __i_68842__ < __len_7466__; __i_68842__++) {
      item = __iter_29213__[__i_68842__];
      len = sup.push(item);
      index = len - 1;
      self.__defineSetter__(index, self._modify_err);
    };
  };
  tuple.prototype._modify_err = function (self) {
    throw ModifyError();
  };
  tuple.prototype.push = null;
  tuple.prototype.pop = null;
  tuple.prototype.shift = null;
  tuple.prototype.unshift = null;
  return tuple;
}();
_null = function (o) {
  return o == null;
};
str = function (o) {
  if (!_null(o) && _typeof(o.toString) === "function") {
    return o.toString();
  } else {
    return "" + o;
  };
};
print = function () {
  var string;
  string = sep.join(function () {
    var __result_31967__, __i_49646__, __len_1606__, __iter_5014__, o;
    __result_31967__ = [];
    for (__i_49646__ = 0, __iter_5014__ = objects, __len_1606__ = __iter_5014__.length; __i_49646__ < __len_1606__; __i_49646__++) {
      o = __iter_5014__[__i_49646__];
      __result_31967__.push(str(o));
    };
    return __result_31967__;
  }()) + end;
  console.log(string);
};
__slice__ = function (ls, lower, upper, step) {
  var idx, length, endidx, ret;
  if (step === null || step === 1) {
    if (upper) {
      return ls.slice(lower || 0, upper);
    } else {
      if (lower) {
        return ls.slice(lower);
      } else {
        return ls.slice();
      };
    };
  } else {
    idx = lower || 0;
    length = len(ls);
    if (upper !== null) {
      endidx = upper;
    } else {
      endidx = length;
    };
    ret = [];
    while (idx < length || idx >= endidx) {
      ret.push(ls[idx]);
      idx += step;
    };
    return ret;
  };
};;

__registermodule__("__main__", function (____main___80957__) {
  ____main___80957__.a = new tuple([1, 2, 3, 4, 5, 6, 7]);
  print(____main___80957__._a = __slice__(____main___80957__.a, null, null, 4));
});

__import__("__main__");

})();