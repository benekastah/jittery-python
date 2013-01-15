
class C:
    def __init__(self, y):
        self.y = y

class B(C):
    a = 5
    def __init__(self, x):
        self.x = x
        super().__init__(x * 2)
