"""
bare module
"""

__import__ = __js__('JITTERY.__import__')


class Exception(Error):

    def __init__(self, msg):
        self.name = self.__class__.__name__
        self.message = msg
        self.stack = __js__('(new Error())').stack


class StopIteration(Exception):
    pass


class Iterator:

    def __iter__(self):
        return self


class IndexableIterator(Iterator):

    def __init__(self, arr):
        self.arr = arr
        self.i = 0

    def __next__(self):
        if i < len(arr):
            result = arr[i]
            i += 1
            return result
        else:
            raise StopIteration()


class range(Iterator):

    def __init__(self, start, stop=None, step=1):
        if stop is None:
            stop, start = start, 0
        self.start = start
        self.stop = stop
        self.step = step
        self._val = self.start

    def __next__(self):
        if self._val >= self.stop:
            raise StopIteration()
        result = self._val
        self._val += self.step
        return result


def iter(it):
    if it and it.__iter__:
        return it.__iter__()
    elif Array.isArray(it):
        return IndexableIterator(it)
    else:
        return IndexableIterator(Object.keys(it))


def next(it):
    return it.__next__()


def hasattr(o, attr):
    return __js__('attr in o')


def len(l):
    if hasattr(l, 'length'):
        return l.length
    else:
        return l.__len__()


def print(*objects):
    console.log.apply(console, objects)


def isinstance(a, b):
    if Array.isArray(b):
        for t_ in b:
            if __js__('a instanceof t_'):
                return True
        return False
    else:
        return __js__('a instanceof b')
