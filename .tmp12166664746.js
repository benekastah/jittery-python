(function () {

var _clone, _each, isinstance, _typeof, __class_instantiate__, object, __class_extend__, Exception, ModifyError, tuple, _null, str, print, __slice__;
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
object = function () {
  __class_extend__(object, object);
  object = function object() {
    return __class_instantiate__(this, arguments);
  };
  __self__.$super = function (parent, self) {
    if (!self.__super__) {
      self.__super__ = __class_instantiate__(null, null, parent, self);
    };
    return self.__super__;
  };
  return object;
}();
__class_extend__ = function (child, parent) {
  child.prototype = _clone(parent.prototype);
  child.prototype.constructor = child;
  child.prototype.super = object.prototype.super.bind(null, parent);
};
Exception = function () {
  __class_extend__(Exception, Error);
  Exception = function Exception() {
    return __class_instantiate__(this, arguments);
  };
  return Exception;
}();
ModifyError = function () {
  __class_extend__(ModifyError, Exception);
  ModifyError = function ModifyError() {
    return __class_instantiate__(this, arguments);
  };
  return ModifyError;
}();
tuple = function () {
  __class_extend__(tuple, Array);
  tuple = function tuple() {
    return __class_instantiate__(this, arguments);
  };
  tuple.prototype.__init__ = function (self, iterable) {
    var __self__, sup, __i_64173__, __len_26039__, __iter_65577__, item, len, index;
    __self__ = arguments[0];
    sup = __self__.$super();
    for (__i_64173__ = 0, __iter_65577__ = iterable, __len_26039__ = __iter_65577__.length; __i_64173__ < __len_26039__; __i_64173__++) {
      item = __iter_65577__[__i_64173__];
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
    var __result_7084__, __i_87983__, __len_44576__, __iter_4384__, o;
    __result_7084__ = [];
    for (__i_87983__ = 0, __iter_4384__ = objects, __len_44576__ = __iter_4384__.length; __i_87983__ < __len_44576__; __i_87983__++) {
      o = __iter_4384__[__i_87983__];
      __result_7084__.push(str(o));
    };
    return __result_7084__;
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

__python__.register_module("__main__", function (____main___77680__) {
  ____main___77680__.a = new tuple([1, 2, 3, 4, 5, 6, 7]);
  print(____main___77680__._a = __slice__(____main___77680__.a, null, null, 4));
});

__import__("__main__");

})();