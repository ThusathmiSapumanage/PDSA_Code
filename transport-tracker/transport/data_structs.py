class MinHeap:
    def __init__(self):
        self._heap = []

    def insert(self, item):
        """Add item to the heap"""
        self._heap.append(item)
        self._heapify_up(len(self._heap) - 1)

    def extract_min(self):
        """Remove and return the smallest item"""
        if self.is_empty():
            raise IndexError("extract_min from empty heap")
        
        if len(self._heap) == 1:
            return self._heap.pop()
        
        # Store the minimum item to return
        min_item = self._heap[0]
        # Move last item to root
        self._heap[0] = self._heap.pop()
        # Restore heap property
        self._heapify_down(0)
        
        return min_item

    def peek_min(self):
        """Return the smallest item without removing it"""
        if self.is_empty():
            return None
        return self._heap[0]

    def is_empty(self):
        """Check if heap is empty"""
        return len(self._heap) == 0

    def size(self):
        """Return number of items in heap"""
        return len(self._heap)

    def _parent_index(self, index):
        """Get parent index"""
        return (index - 1) // 2

    def _left_child_index(self, index):
        """Get left child index"""
        return 2 * index + 1

    def _right_child_index(self, index):
        """Get right child index"""
        return 2 * index + 2

    def _swap(self, i, j):
        """Swap items at two positions"""
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _heapify_up(self, index):
        """Move item up to maintain heap property"""
        while index > 0:
            parent_idx = self._parent_index(index)
            # Compare first element of tuple (for your datetime tuples)
            if self._heap[index][0] >= self._heap[parent_idx][0]:
                break
            self._swap(index, parent_idx)
            index = parent_idx

    def _heapify_down(self, index):
        """Move item down to maintain heap property"""
        heap_size = len(self._heap)
        
        while True:
            smallest_idx = index
            left_idx = self._left_child_index(index)
            right_idx = self._right_child_index(index)
            
            # Find smallest among parent and children
            if (left_idx < heap_size and 
                self._heap[left_idx][0] < self._heap[smallest_idx][0]):
                smallest_idx = left_idx
                
            if (right_idx < heap_size and 
                self._heap[right_idx][0] < self._heap[smallest_idx][0]):
                smallest_idx = right_idx
            
            # If parent is smallest, heap property is satisfied
            if smallest_idx == index:
                break
                
            # Otherwise, swap and continue
            self._swap(index, smallest_idx)
            index = smallest_idx

    # Keep compatibility with existing code
    def push(self, item):
        self.insert(item)
    
    def pop(self):
        return self.extract_min()
    
    def peek(self):
        return self.peek_min()
    
    def empty(self):
        return self.is_empty()

class Queue:
    def __init__(self):
        self._items = []
        self._front_index = 0

    def enqueue(self, item):
        """Add item to the back of the queue"""
        self._items.append(item)

    def dequeue(self):
        """Remove and return item from the front of the queue"""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        
        item = self._items[self._front_index]
        self._front_index += 1
        
        # Clean up when too much space is wasted
        if self._front_index > 32 and self._front_index * 2 > len(self._items):
            self._items = self._items[self._front_index:]
            self._front_index = 0
            
        return item

    def front(self):
        """Return front item without removing it"""
        if self.is_empty():
            return None
        return self._items[self._front_index]

    def rear(self):
        """Return rear item without removing it"""
        if self.is_empty():
            return None
        return self._items[-1]

    def is_empty(self):
        """Check if queue is empty"""
        return self._front_index >= len(self._items)

    def size(self):
        """Return number of items in queue"""
        return len(self._items) - self._front_index

    # Keep compatibility with existing code
    def push(self, item):
        self.enqueue(item)
    
    def pop(self):
        return self.dequeue()
    
    def empty(self):
        return self.is_empty()
    
    def __len__(self):
        return self.size()
