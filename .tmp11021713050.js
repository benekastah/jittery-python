(function () {

var _each, isinstance, _clone, _typeof, __class_instantiate__, _super, __class_extend__, Exception, ModifyError, tuple, _null, str, print, __slice__;
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
    var __self__, sup, __i_71028__, __len_33752__, __iter_83813__, item, len, index;
    __self__ = arguments[0];
    sup = __self__.$super();
    for (__i_71028__ = 0, __iter_83813__ = iterable, __len_33752__ = __iter_83813__.length; __i_71028__ < __len_33752__; __i_71028__++) {
      item = __iter_83813__[__i_71028__];
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
    var __result_79518__, __i_85252__, __len_18170__, __iter_80185__, o;
    __result_79518__ = [];
    for (__i_85252__ = 0, __iter_80185__ = objects, __len_18170__ = __iter_80185__.length; __i_85252__ < __len_18170__; __i_85252__++) {
      o = __iter_80185__[__i_85252__];
      __result_79518__.push(str(o));
    };
    return __result_79518__;
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

__python__.register_module("__main__", function (____main___44973__) {
  ____main___44973__.a = new tuple([1, 2, 3, 4, 5, 6, 7]);
  print(____main___44973__._a = __slice__(____main___44973__.a, null, null, 4));
});

__import__("__main__");

})();