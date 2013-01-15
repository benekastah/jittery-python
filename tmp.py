
FunctionDef(
    name='__slice__',
    args=arguments(
        args=[
            arg(arg='ls', annotation=None),
            arg(arg='lower', annotation=None),
            arg(arg='upper', annotation=None),
            arg(arg='step', annotation=None)
        ],
        vararg=None,
        varargannotation=None,
        kwonlyargs=[],
        kwarg=None,
        kwargannotation=None,
        defaults=[Num(n=1)],
        kw_defaults=[]
    ),
    body=[
        If(test=Compare(left=Name(id='lower', ctx=Load()), ops=[Lt()], comparators=[Num(n=0)]),
           body=[AugAssign(target=Name(id='lower', ctx=Store()), op=Add(), value=Call(func=Name(id='len', ctx=Load()), args=[Name(id='ls', ctx=Load())], keywords=[], starargs=None, kwargs=None))],
           orelse=[]),
        If(test=Compare(left=Name(id='upper', ctx=Load()), ops=[Lt()], comparators=[Num(n=0)]),
           body=[AugAssign(target=Name(id='upper', ctx=Store()), op=Add(), value=Call(func=Name(id='len', ctx=Load()), args=[Name(id='ls', ctx=Load())], keywords=[], starargs=None, kwargs=None))],
           orelse=[]),
        If(test=BoolOp(op=Or(), values=[BoolOp(op=And(), values=[Compare(left=Call(func=Name(id='_typeof', ctx=Load()), args=[Name(id='ls', ctx=Load())], keywords=[], starargs=None, kwargs=None), ops=[Is()], comparators=[Str(s='array')]), Compare(left=Name(id='step', ctx=Load()), ops=[Is()], comparators=[Name(id='None', ctx=Load())])]), Compare(left=Name(id='step', ctx=Load()), ops=[Is()], comparators=[Num(n=1)])]),
           body=[If(test=Name(id='upper', ctx=Load()), body=[Return(value=Call(func=Attribute(value=Name(id='ls', ctx=Load()), attr='slice', ctx=Load()), args=[BoolOp(op=Or(), values=[Name(id='lower', ctx=Load()), Num(n=0)]), Name(id='upper', ctx=Load())], keywords=[], starargs=None, kwargs=None))], orelse=[If(test=Name(id='lower', ctx=Load()), body=[Return(value=Call(func=Attribute(value=Name(id='ls', ctx=Load()), attr='slice', ctx=Load()), args=[Name(id='lower', ctx=Load())], keywords=[], starargs=None, kwargs=None))], orelse=[Return(value=Call(func=Attribute(value=Name(id='ls', ctx=Load()), attr='slice', ctx=Load()), args=[], keywords=[], starargs=None, kwargs=None))])])],
           orelse=[Assign(targets=[Name(id='idx', ctx=Store())], value=BoolOp(op=Or(), values=[Name(id='lower', ctx=Load()), Num(n=0)])), Assign(targets=[Name(id='length', ctx=Store())], value=Call(func=Name(id='len', ctx=Load()), args=[Name(id='ls', ctx=Load())], keywords=[], starargs=None, kwargs=None)), If(test=Compare(left=Name(id='upper', ctx=Load()), ops=[IsNot()], comparators=[Name(id='None', ctx=Load())]), body=[Assign(targets=[Name(id='endidx', ctx=Store())], value=Name(id='upper', ctx=Load()))], orelse=[Assign(targets=[Name(id='endidx', ctx=Store())], value=Name(id='length', ctx=Load()))]), Assign(targets=[Name(id='ret', ctx=Store())], value=List(elts=[], ctx=Load())), While(test=BoolOp(op=And(), values=[Compare(left=Name(id='idx', ctx=Load()), ops=[GtE()], comparators=[Num(n=0)]), BoolOp(op=Or(), values=[Compare(left=Name(id='idx', ctx=Load()), ops=[Lt()], comparators=[Name(id='length', ctx=Load())]), Compare(left=Name(id='idx', ctx=Load()), ops=[GtE()], comparators=[Name(id='endidx', ctx=Load())])])]), body=[Expr(value=Call(func=Name(id='jseval', ctx=Load()), args=[Str(s='ret.push(ls[idx])')], keywords=[], starargs=None, kwargs=None)), AugAssign(target=Name(id='idx', ctx=Store()), op=Add(), value=Name(id='step', ctx=Load()))], orelse=[]), Return(value=Name(id='ret', ctx=Load()))])],
    decorator_list=[],
    returns=None)
