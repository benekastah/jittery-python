import ast
import os
import re


def parse_expr(expr):
    module = ast.parse(expr)
    try:
        node = ast.parse(expr)
    except SyntaxError:
        assert False
    assert isinstance(node, ast.Module)
    assert len(node.body) == 1
    assert isinstance(node.body[0], ast.Expr)

    return node.body[0].value


def validate_module_name(module_name):
    expr = parse_expr(module_name)
    for body in ast.walk(expr):
        assert isinstance(body, (ast.Name, ast.Attribute, ast.Load))


def find_files(start, extension='.py'):
    for dirpath, _, filenames, _ in os.fwalk(start):
        for filename in filenames:
            if filename.endswith(extension):
                yield os.path.join(dirpath, filename)


def get_module_name(base_dir, filename, extension='.py'):
    if not base_dir:
        return '__main__'
    base_dir = os.path.join(base_dir, '')
    module_name = filename[len(base_dir):-len(extension)]
    module_name = re.sub(r'/', '.', module_name)
    try:
        validate_module_name(module_name)
    except AssertionError:
        raise Exception('Invalid filename for module: {}'.format(filename))
    return module_name


def get_modules(*package_dirs, extension='.py'):
    for base_dir in package_dirs:
        if os.path.isdir(base_dir):
            for filename in find_files(base_dir, extension):
                yield filename, get_module_name(base_dir, filename, extension)
        else:
            yield base_dir, get_module_name('', base_dir, extension)
