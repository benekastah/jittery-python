import ast

def print_node(node):
    print(ast.dump(node))

def dict_to_ast(d):
    keys = []
    vals = []
    for k, v in d:
        keys.append(k)
        vals.append(v)
    return ast.Dict(keys, vals)

def list_to_ast(ls):
    return ast.List(ls, None)

def num_to_ast(n):
    return ast.Num(n)

def str_to_ast(s):
    return ast.Str(s)

def keywords_to_dict(kwds):
    keys = []
    vals = []
    for k in kwds:
        keys.append(k.arg)
        vals.append(k.value)
    return ast.Dict(keys, vals)

javascript_reserved_words = (
    "break",
    "case",
    "catch",
    "continue",
    # "debugger",
    "default",
    "delete",
    "do",
    "else",
    "finally",
    "for",
    "function",
    "if",
    "in",
    "instanceof",
    "new",
    "return",
    "switch",
    "this",
    "throw",
    "try",
    "typeof",
    "var",
    "void",
    "while",
    "with",
    "class",
    "enum",
    "export",
    "extends",
    "import",
    "super",
    "implements",
    "interface",
    "let",
    "package",
    "private",
    "protected",
    "public",
    "static",
    "yield",
)

python_keywords = {
    'True': 'true',
    'False': 'false',
    'None': 'null',
}
