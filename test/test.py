
class range:

    def __init__(self, start, stop=None, step=1):
        if stop is None:
            stop, start = start, 0
        self.start = start
        self.stop = stop
        self.step = step
        self._val = self.start
