

def fn(a, b, *args, **kwargs):
    print('a = ', a)
    print('b = ', b)
    print('*args = ', args)
    print('**kwargs = ', kwargs)


fn(1, 2, 3, 4, 5, 6, f=1, g=2)


for i in range(10):
    print(i)


print('range(2, 12, 2)')
for i in range(2, 12, 2):
    print(i)
