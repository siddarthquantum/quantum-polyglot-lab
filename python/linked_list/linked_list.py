"""Singly linked list in Python: traverse, insert, delete, search, reverse, middle, cycle.

Same algorithm as the C version. Python has no pointers you can see, but object
references behave the same way: ``node.next`` holds a reference to another Node,
and ``None`` marks the end. Memory is reclaimed by reference counting plus a
cycle collector, so there is no free() and no manual cleanup.

The node walking is written by hand on purpose so the O(n) work is visible.
Real Python code would use ``collections.deque``, which gives O(1) at both ends
with none of this bookkeeping (see the benchmark note in the shared README).

    python3 python/linked_list/linked_list.py         -> step-by-step demo
    python3 python/linked_list/linked_list.py bench   -> timing run
"""

import sys
import time


class ListOpError(Exception):
    """Raised for invalid operations (empty, bad position, missing value)."""


class Node:
    """One element. __slots__ keeps each node small and attribute access fast."""

    __slots__ = ("value", "next")

    def __init__(self, value: int, nxt: "Node | None" = None) -> None:
        self.value = value
        self.next = nxt


class LinkedList:
    def __init__(self) -> None:
        self.head: Node | None = None  # None means empty
        self.len = 0  # kept in sync so __len__ is O(1)

    def __len__(self) -> int:
        return self.len

    def __str__(self) -> str:
        # TRAVERSE: follow .next until None. Time O(n), extra space O(n) for the text.
        parts = []
        cur = self.head
        while cur is not None:
            parts.append(str(cur.value))
            cur = cur.next
        return "[" + ", ".join(parts) + f"]  len={self.len}"

    def insert(self, pos: int, value: int) -> None:
        """Insert at pos (0 <= pos <= len). Time O(1) at head, O(n) otherwise. Space O(1)."""
        # Python would happily accept pos = -1 (it means "from the end" for
        # sequences), so we must reject negative positions ourselves.
        if pos < 0 or pos > self.len:
            raise ListOpError("position out of range")
        if pos == 0:
            self.head = Node(value, self.head)  # new node points at old head
        else:
            prev = self.head
            for _ in range(pos - 1):
                prev = prev.next  # type: ignore[union-attr]
            prev.next = Node(value, prev.next)  # type: ignore[union-attr]
        self.len += 1

    def delete_at(self, pos: int) -> int:
        """Delete and return the value at pos (0 <= pos < len). Time O(n) worst. Space O(1)."""
        if self.len == 0:
            raise ListOpError("list is empty")
        if pos < 0 or pos >= self.len:
            raise ListOpError("position out of range")
        if pos == 0:
            victim = self.head
            self.head = victim.next  # type: ignore[union-attr]
        else:
            prev = self.head
            for _ in range(pos - 1):
                prev = prev.next  # type: ignore[union-attr]
            victim = prev.next  # type: ignore[union-attr]
            prev.next = victim.next  # type: ignore[union-attr]
        victim.next = None  # type: ignore[union-attr]  # unlink fully; refcount drops to 0
        self.len -= 1
        return victim.value  # type: ignore[union-attr]

    def delete_value(self, value: int) -> None:
        """Delete the first node holding value. Time O(n), extra space O(1)."""
        if self.len == 0:
            raise ListOpError("list is empty")
        prev = None
        cur = self.head
        while cur is not None and cur.value != value:
            prev = cur
            cur = cur.next
        if cur is None:
            raise ListOpError("value not found")
        if prev is None:
            self.head = cur.next
        else:
            prev.next = cur.next
        cur.next = None
        self.len -= 1

    def search(self, value: int) -> int:
        """Index of the first node holding value, or -1. Time O(n)."""
        i = 0
        cur = self.head
        while cur is not None:
            if cur.value == value:
                return i
            cur = cur.next
            i += 1
        return -1

    def get(self, pos: int) -> int:
        """Value at pos. Time O(n) -- on a list/array this would be O(1)."""
        if pos < 0 or pos >= self.len:
            raise ListOpError("position out of range")
        cur = self.head
        for _ in range(pos):
            cur = cur.next  # type: ignore[union-attr]
        return cur.value  # type: ignore[union-attr]

    def reverse(self) -> None:
        """Reverse in place by flipping every .next. Time O(n), extra space O(1)."""
        prev = None
        cur = self.head
        while cur is not None:
            nxt = cur.next  # save before overwriting, or the rest is lost
            cur.next = prev
            prev = cur
            cur = nxt
        self.head = prev

    def middle(self) -> int:
        """Middle value via two pointers. Time O(n), extra space O(1).

        For an even length this returns the SECOND of the two middle nodes.
        """
        if self.head is None:
            raise ListOpError("list is empty")
        slow = self.head
        fast: Node | None = self.head
        while fast is not None and fast.next is not None:
            slow = slow.next  # type: ignore[assignment]
            fast = fast.next.next
        return slow.value

    def has_cycle(self) -> bool:
        """Floyd's algorithm. Time O(n), extra space O(1) -- no 'visited' set needed."""
        slow = self.head
        fast = self.head
        while fast is not None and fast.next is not None:
            slow = slow.next  # type: ignore[union-attr]
            fast = fast.next.next
            if slow is fast:  # identity, not equality: same object
                return True
        return False

    def clear(self) -> None:
        """Drop the chain. Time O(n) as refcounts fall; O(1) of our own work."""
        cur = self.head
        while cur is not None:
            nxt = cur.next
            cur.next = None
            cur = nxt
        self.head = None
        self.len = 0


# --------------------------------------------------------------------- demo


def _show_state(ll: LinkedList, label: str) -> None:
    print(f"{label:<17}: {ll}")


def _show_insert(ll: LinkedList, label: str, pos: int, value: int) -> None:
    try:
        ll.insert(pos, value)
        print(f"{label:<17}: {ll}")
    except ListOpError as e:
        print(f"{label:<17}: error: {e}")


def _show_delete_at(ll: LinkedList, label: str, pos: int) -> None:
    try:
        removed = ll.delete_at(pos)
        print(f"{label:<17}: removed {removed} -> {ll}")
    except ListOpError as e:
        print(f"{label:<17}: error: {e}")


def _show_delete_value(ll: LinkedList, label: str, value: int) -> None:
    try:
        ll.delete_value(value)
        print(f"{label:<17}: removed -> {ll}")
    except ListOpError as e:
        print(f"{label:<17}: error: {e}")


def _show_get(ll: LinkedList, label: str, pos: int) -> None:
    try:
        print(f"{label:<17}: {ll.get(pos)}")
    except ListOpError as e:
        print(f"{label:<17}: error: {e}")


def _show_search(ll: LinkedList, label: str, value: int) -> None:
    idx = ll.search(value)
    found = f"found at index {idx}" if idx >= 0 else "not found"
    print(f"{label:<17}: {found}")


def demo() -> None:
    ll = LinkedList()

    print("=== Linked list demo (singly linked) ===")
    _show_state(ll, "start")

    _show_insert(ll, "push_front 30", 0, 30)
    _show_insert(ll, "push_front 20", 0, 20)
    _show_insert(ll, "push_front 10", 0, 10)
    _show_insert(ll, "push_back 40", ll.len, 40)
    _show_insert(ll, "push_back 50", ll.len, 50)

    values = []
    cur = ll.head
    while cur is not None:
        values.append(str(cur.value))
        cur = cur.next
    print(f"{'traverse':<17}: " + " ".join(values))

    _show_get(ll, "get at 3", 3)
    _show_get(ll, "get at 9", 9)
    _show_search(ll, "search 30", 30)
    _show_search(ll, "search 77", 77)

    _show_insert(ll, "insert 99 at 2", 2, 99)
    _show_insert(ll, "insert 5 at 0", 0, 5)
    _show_insert(ll, "insert 60 at end", ll.len, 60)
    _show_insert(ll, "insert 7 at -1", -1, 7)

    _show_delete_at(ll, "delete at 3", 3)
    _show_delete_at(ll, "pop_front", 0)
    _show_delete_at(ll, "pop_back", ll.len - 1)
    _show_delete_value(ll, "delete value 30", 30)
    _show_delete_value(ll, "delete value 77", 77)
    _show_delete_at(ll, "delete at 9", 9)

    print(f"{'middle':<17}: {ll.middle()}")

    ll.reverse()
    _show_state(ll, "reverse")

    print(f"{'has cycle':<17}: {str(ll.has_cycle()).lower()}")

    ll.clear()
    _show_state(ll, "clear")
    _show_delete_at(ll, "pop_front", 0)


# ---------------------------------------------------------------- benchmark

BUILD_N = 200_000
PASSES = 10
IDX_N = 20_000
IDX_GETS = 200
ROUNDS = 3


def bench() -> None:
    # Python's recursion limit is irrelevant here (everything is iterative), but
    # building 200k nodes does show the cost of one object per element.
    best_b = best_t = best_g = best_p = float("inf")
    sum_b = sum_t = sum_g = sum_p = 0

    for _ in range(ROUNDS):
        ll = LinkedList()

        t0 = time.perf_counter()
        for i in range(BUILD_N):
            ll.insert(0, i)
        best_b = min(best_b, (time.perf_counter() - t0) * 1e3)
        sum_b = 0
        cur = ll.head
        while cur is not None:
            sum_b += cur.value
            cur = cur.next

        t0 = time.perf_counter()
        sum_t = 0
        for _pass in range(PASSES):
            cur = ll.head
            while cur is not None:
                sum_t += cur.value
                cur = cur.next
        best_t = min(best_t, (time.perf_counter() - t0) * 1e3)

        t0 = time.perf_counter()
        sum_p = 0
        step = 1
        while ll.len > 0:
            sum_p += step * ll.delete_at(0)
            step += 1
        best_p = min(best_p, (time.perf_counter() - t0) * 1e3)

        g = LinkedList()
        for i in range(IDX_N):
            g.insert(0, i)
        t0 = time.perf_counter()
        sum_g = 0
        for k in range(IDX_GETS):
            sum_g += g.get((k * 97) % IDX_N)
        best_g = min(best_g, (time.perf_counter() - t0) * 1e3)
        g.clear()

    print(f"build_front   checksum={sum_b} time_ms={best_b:.3f}")
    print(f"traverse      checksum={sum_t} time_ms={best_t:.3f}")
    print(f"index_access  checksum={sum_g} time_ms={best_g:.3f}")
    print(f"pop_front     checksum={sum_p} time_ms={best_p:.3f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "bench":
        bench()
    else:
        demo()
