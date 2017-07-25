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
