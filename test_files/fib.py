"""
Test that we can use generator functions and the yield keyword
"""

def fib(n):
    a = 0
    b = 1
    result = []
    for _ in range(n):
        try:
            result.push(b)
        except:
            result.append(b)
        a, b = b, a + b
    return result


if __name__ == '__main__':
    for n in fib():
        print(n)
