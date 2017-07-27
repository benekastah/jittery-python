
def combine(a, b):
    yield from a
    yield from b


if __name__ == '__main__':
    for x in combine([1, 2, 3], ('a', 'b', 'c')):
        print(x)
