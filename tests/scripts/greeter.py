class Greeter:
    def __init__(self, greeterName):
        self.greeterName = greeterName

    def greet(self, name):
        print("I,", self.greeterName + ",", "hereby greet thee,", name + ".")

g = Greeter("Jameson III")
g.greet("Paul")
