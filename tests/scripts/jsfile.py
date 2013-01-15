from jsfile2 import B

class A(B):
    def __init__(self):
        super().__init__(10)


a = A()
print(a.a, a.x, a.y)
