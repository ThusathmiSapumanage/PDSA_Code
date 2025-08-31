class Queue:
    def __init__(self):
        self._data = []
        self._head = 0

    def push(self, x): self._data.append(x)

    def pop(self):
        if self.empty(): raise IndexError("pop from empty queue")
        x = self._data[self._head]
        self._head += 1
        if self._head > 32 and self._head * 2 > len(self._data):
            self._data = self._data[self._head:]
            self._head = 0
        return x

    def front(self):
        return None if self.empty() else self._data[self._head]

    def empty(self): return self._head >= len(self._data)

    def __len__(self): return len(self._data) - self._head


class Stack:
    def __init__(self, maxlen=None):
        self._data = []
        self._maxlen = maxlen

    def push(self, x):
        self._data.append(x)
        if self._maxlen and len(self._data) > self._maxlen:
            self._data.pop(0)

    def pop(self):
        if self.empty(): raise IndexError("pop from empty stack")
        return self._data.pop()

    def peek(self): return None if self.empty() else self._data[-1]
    def empty(self): return len(self._data) == 0
    def __len__(self): return len(self._data)

class MinHeap:
    def __init__(self):
        self._a = []

    def _parent(self, i): return (i - 1) // 2
    def _left(self, i): return 2 * i + 1
    def _right(self, i): return 2 * i + 2

    def _swap(self, i, j): self._a[i], self._a[j] = self._a[j], self._a[i]

    def push(self, item):
        self._a.append(item)
        self._sift_up(len(self._a) - 1)

    def pop(self):
        if self.empty(): raise IndexError("pop from empty heap")
        self._swap(0, len(self._a) - 1)
        x = self._a.pop()
        if not self.empty(): self._sift_down(0)
        return x

    def peek(self): return None if self.empty() else self._a[0]
    def empty(self): return len(self._a) == 0

    def _sift_up(self, i):
        while i > 0:
            p = self._parent(i)
            if self._a[i][0] < self._a[p][0]:
                self._swap(i, p); i = p
            else:
                break

    def _sift_down(self, i):
        n = len(self._a)
        while True:
            l, r = self._left(i), self._right(i)
            s = i
            if l < n and self._a[l][0] < self._a[s][0]: s = l
            if r < n and self._a[r][0] < self._a[s][0]: s = r
            if s != i: self._swap(i, s); i = s
            else: break

# Lochana
class HashMap:
    def __init__(self):
        self._map = {}

    def set(self, k, v): self._map[k] = v
    def get(self, k, default=None): return self._map.get(k, default)
    def has(self, k): return k in self._map
    def delete(self, k): self._map.pop(k, None)
    def keys(self): return list(self._map.keys())
    def values(self): return list(self._map.values())
    def items(self): return list(self._map.items())
    def __len__(self): return len(self._map)
    def __iter__(self): return iter(self._map.items())

