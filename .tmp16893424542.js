(function () {

var _each, isinstance, _clone, _typeof, __class_instantiate__, _super, __class_extend__, object, __ModuleList__, __registermodule__, _null, str, print;
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
__class_instantiate__ = function (cls, self, args, child_self) {
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
    self.__super__ = __class_instantiate__(parent, null, null, self);
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
    return __class_instantiate__(object, this, arguments);
  };
  object.prototype.__init__ = function (self) {
    ;
  };
  return object;
}();
__ModuleList__ = function () {
  __class_extend__(__ModuleList__, object);
  function __ModuleList__() {
    return __class_instantiate__(__ModuleList__, this, arguments);
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
  return __ModuleList__();
  return __ModuleList__;
}();
__registermodule__ = function (name, fn) {
  __ModuleList__.__register__(name, fn);
};
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
    var __result_41590__, __i_3751__, __len_28523__, __iter_17177__, o;
    __result_41590__ = [];
    for (__i_3751__ = 0, __iter_17177__ = objects, __len_28523__ = __iter_17177__.length; __i_3751__ < __len_28523__; __i_3751__++) {
      o = __iter_17177__[__i_3751__];
      __result_41590__.push(str(o));
    };
    return __result_41590__;
  }()) + end;
  console.log(string);
};;

__registermodule__("__main__", function (____main___51788__) {
  print(____main___51788__.o = object());
});

__import__("__main__");

})();