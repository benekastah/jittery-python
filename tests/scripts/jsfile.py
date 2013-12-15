# from jsfile2 import B

# class A(B):
#   def __init__(self):
#     super().__init__(10)

# a = A()
# print(a.a, a.x, a.y)

ls = list()
ls.append(3)
print(ls)

tp = tuple([1, 2, 3, 4])
print(tp)


class A:
  a = 5
  b = a + 2
  def c(self):
    return a + b

a = A()
print(a.a, a.b)
a.c()
