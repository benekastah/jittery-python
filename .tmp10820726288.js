(function () {

var _each, isinstance, _clone, _typeof, __class_instantiate__, _super, __class_extend__, object, _null, str, print, __ModuleList__, __registermodule__, Exception, ModifyError, tuple, __slice__;
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
    var __result_50536__, __i_44347__, __len_59464__, __iter_98407__, o;
    __result_50536__ = [];
    for (__i_44347__ = 0, __iter_98407__ = objects, __len_59464__ = __iter_98407__.length; __i_44347__ < __len_59464__; __i_44347__++) {
      o = __iter_98407__[__i_44347__];
      __result_50536__.push(str(o));
    };
    return __result_50536__;
  }()) + end;
  console.log(string);
};
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
    print(__ModuleList__);
  } catch (__err_93656__) {
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
    var __self__, sup, __i_31767__, __len_36710__, __iter_96729__, item, len, index;
    __self__ = arguments[0];
    sup = __self__.$super();
    for (__i_31767__ = 0, __iter_96729__ = iterable, __len_36710__ = __iter_96729__.length; __i_31767__ < __len_36710__; __i_31767__++) {
      item = __iter_96729__[__i_31767__];
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

__registermodule__("__main__", function (____main___10614__) {
  ____main___10614__.a = new tuple([1, 2, 3, 4, 5, 6, 7]);
  print(____main___10614__._a = __slice__(____main___10614__.a, null, null, 4));
});

__import__("__main__");

})();