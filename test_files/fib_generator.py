"""
Test that we can use generator functions and the yield keyword
"""

def fib():
    a = 0
    b = 1
    while 1:
        yield b
        a, b = b, a + b


if __name__ == '__main__':
    for _, n in zip(range(10), fib()):
        print(n)
