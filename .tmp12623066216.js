(function () {

var _each, isinstance, _clone, _typeof, __class_instantiate__, _super, __class_extend__, object, _null, str, print, __ModuleList__, __registermodule__;
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
    var __result_79797__, __i_79101__, __len_26059__, __iter_30237__, o;
    __result_79797__ = [];
    for (__i_79101__ = 0, __iter_30237__ = objects, __len_26059__ = __iter_30237__.length; __i_79101__ < __len_26059__; __i_79101__++) {
      o = __iter_30237__[__i_79101__];
      __result_79797__.push(str(o));
    };
    return __result_79797__;
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
  } catch (__err_96103__) {
    ;
  };
  return __ModuleList__;
}();
__registermodule__ = function (name, fn) {
  __ModuleList__.__register__(name, fn);
};;

__registermodule__("__main__", function (____main___4969__) {
  print(____main___4969__.o = object());
});

__import__("__main__");

})();