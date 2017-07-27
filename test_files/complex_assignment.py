

if __name__ == '__main__':
    a, *b, c = [1, 2, 3, 4]
    print(a, b, c)
    a = b, c = (1, 2)
    print(a, b, c)
    a, (b, *c), *d, e = [1, (2, 3, 4), 5, 6, 7, 8]
    print(a, b, c, d, e)
