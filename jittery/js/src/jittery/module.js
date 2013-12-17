(function (undefined) {

  goog.provide('jittery.module.module');
  goog.provide('jittery.module.ImportError');
  goog.provide('jittery.module.__register_module__');
  goog.provide('jittery.module.__import__');

  var available_modules = {};

  var resolved_modules = {};

  function module() {}
  jittery.module.module = module;

  var ImportError = jittery.module.ImportError = (function () {
    goog.inherits(ImportError, Error);

    function ImportError(name, globals, locals, fromlist, level) {
      this.constructor.super_.apply(this, 'Failed to import ' + name);
    }

    ImportError.prototype.name = 'ImportError';

    return ImportError;
  })();

  jittery.module.__register_module__ = function (name, fn) {
    available_modules[name] = fn;
  };

  jittery.module.__import__ = function (name, globals, locals, fromlist, level) {
    if (fromlist === undefined) {
      fromlist = [];
    }
    if (level === undefined) {
      level = 0;
    }
    if (!(name in resolved_modules)) {
      if (!(name in available_modules)) {
        throw new ImportError(name, globals, locals, fromlist, level);
      }
      resolved_modules[name] = new module;
      available_modules[name](resolved_modules[name]);
    }
    return resolved_modules[name];
  };

})();
