"""Doubly linked list in Python: both ends O(1), held-node removal, reverse, integrity check.

Same algorithm as the C version. Each node holds references to BOTH neighbours,
which makes a doubly linked list a structure full of reference cycles
(a.next is b, b.prev is a). CPython's reference counting alone can never free
such a cycle; its cycle collector has to find it. clear() below breaks the
links explicitly so memory is returned immediately instead of at the next
collection.

Real Python code would use ``collections.deque`` (a C-implemented doubly linked
list of fixed-size blocks) for O(1) work at both ends. This file writes the
node handling out by hand so every link change is visible.

    python3 python/doubly_linked_list/doubly_linked_list.py         -> step-by-step demo
    python3 python/doubly_linked_list/doubly_linked_list.py bench   -> timing run
"""

import sys
import time

EMPTY = "list is empty"
RANGE = "position out of range"
NOT_FOUND = "value not found"
CORRUPT = "corrupted double-linked list"


class ListOpError(Exception):
    """Raised for invalid operations. Messages match the other three languages."""


class Node:
    """One element and the handle type: holding a Node lets you remove it in O(1)."""

    __slots__ = ("value", "prev", "next")

    def __init__(self, value: int) -> None:
        self.value = value
        self.prev: Node | None = None
        self.next: Node | None = None


class DoublyLinkedList:
    def __init__(self) -> None:
        self.head: Node | None = None
        self.tail: Node | None = None
        self.len = 0
        # Set by _node_at() so the demo can show which end the walk started from.
        self.last_from_head = True
        self.last_steps = 0

    def __len__(self) -> int:
        return self.len

    def __str__(self) -> str:
        parts = []
        cur = self.head
        while cur is not None:
            parts.append(str(cur.value))
            cur = cur.next
        return "[" + ", ".join(parts) + f"]  len={self.len}"

    def push_front(self, value: int) -> Node:
        """O(1)."""
        n = Node(value)
        n.next = self.head
        if self.head is not None:
            self.head.prev = n
        else:
            self.tail = n
        self.head = n
        self.len += 1
        return n

    def push_back(self, value: int) -> Node:
        """O(1) because we keep a tail reference."""
        n = Node(value)
        n.prev = self.tail
        if self.tail is not None:
            self.tail.next = n
        else:
            self.head = n
        self.tail = n
        self.len += 1
        return n

    def _node_at(self, pos: int) -> Node:
        """Walk from the nearer end. O(min(pos, len-1-pos)). Caller checks bounds."""
        if pos < self.len - pos:
            self.last_from_head, self.last_steps = True, pos
            cur = self.head
            for _ in range(pos):
                cur = cur.next  # type: ignore[union-attr]
        else:
            self.last_from_head, self.last_steps = False, self.len - 1 - pos
            cur = self.tail
            for _ in range(self.last_steps):
                cur = cur.prev  # type: ignore[union-attr]
        return cur  # type: ignore[return-value]

    def get(self, pos: int) -> int:
        """O(min(pos, n-pos))."""
        # Python would accept -1 on a real sequence; a list position must not.
        if pos < 0 or pos >= self.len:
            raise ListOpError(RANGE)
        return self._node_at(pos).value

    def insert(self, pos: int, value: int) -> None:
        """Insert before the node currently at pos (0 <= pos <= len)."""
        if pos < 0 or pos > self.len:
            raise ListOpError(RANGE)
        if pos == 0:
            self.push_front(value)
            return
        if pos == self.len:
            self.push_back(value)
            return
        succ = self._node_at(pos)
        n = Node(value)
        n.prev, n.next = succ.prev, succ  # 1. new node points at both neighbours
        succ.prev.next = n  # type: ignore[union-attr]  # 2. neighbours point at it
        succ.prev = n
        self.len += 1

    def remove_node(self, node: Node) -> int:
        """Remove a held node in O(1), after glibc's safe-unlink neighbour check."""
        if (node.prev.next is not node) if node.prev is not None else (self.head is not node):
            raise ListOpError(CORRUPT)
        if (node.next.prev is not node) if node.next is not None else (self.tail is not node):
            raise ListOpError(CORRUPT)
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.prev = node.next = None
        self.len -= 1
        return node.value

    def pop_front(self) -> int:
        """O(1)."""
        if self.head is None:
            raise ListOpError(EMPTY)
        return self.remove_node(self.head)

    def pop_back(self) -> int:
        """O(1) -- the operation a singly linked list cannot do cheaply."""
        if self.tail is None:
            raise ListOpError(EMPTY)
        return self.remove_node(self.tail)

    def delete_at(self, pos: int) -> int:
        """Nearer-end walk plus O(1) unlink."""
        if self.len == 0:
            raise ListOpError(EMPTY)
        if pos < 0 or pos >= self.len:
            raise ListOpError(RANGE)
        return self.remove_node(self._node_at(pos))

    def find(self, value: int) -> Node | None:
        """The node holding value, or None. O(n). This is how you get a handle."""
        cur = self.head
        while cur is not None:
            if cur.value == value:
                return cur
            cur = cur.next
        return None

    def search(self, value: int) -> int:
        """Index of the first node holding value, or -1. O(n)."""
        i = 0
        cur = self.head
        while cur is not None:
            if cur.value == value:
                return i
            cur = cur.next
            i += 1
        return -1

    def delete_value(self, value: int) -> None:
        if self.len == 0:
            raise ListOpError(EMPTY)
        n = self.find(value)
        if n is None:
            raise ListOpError(NOT_FOUND)
        self.remove_node(n)

    def reverse(self) -> None:
        """Swap prev/next on every node, then swap head and tail. O(n), O(1) space."""
        cur = self.head
        while cur is not None:
            cur.prev, cur.next = cur.next, cur.prev
            cur = cur.prev  # the old next
        self.head, self.tail = self.tail, self.head

    def check(self) -> int:
        """-2 when consistent, -1 if corrupt with no single culprit, else first bad index.

        O(n), capped at len + 1 steps so a cycle cannot hang the check.
        """
        if (self.head is None) != (self.tail is None):
            return -1
        if self.head is not None and self.head.prev is not None:
            return 0
        i = 0
        prev = None
        cur = self.head
        while cur is not None:
            if i > self.len or cur.prev is not prev:
                return i
            prev, cur = cur, cur.next
            i += 1
        if prev is not self.tail or i != self.len:
            return i
        return -2

    def clear(self) -> None:
        """Break every link so refcounts reach zero now, not at the next GC cycle."""
        cur = self.head
        while cur is not None:
            nxt = cur.next
            cur.prev = cur.next = None
            cur = nxt
        self.head = self.tail = None
        self.len = 0


# --------------------------------------------------------------------- demo


def _line(label: str, text: str) -> None:
    print(f"{label:<17}: {text}")


def _show(ll: DoublyLinkedList, label: str, op) -> None:
    try:
        op()
        _line(label, str(ll))
    except ListOpError as e:
        _line(label, f"error: {e}")


def _show_removed(ll: DoublyLinkedList, label: str, op) -> None:
    try:
        removed = op()
        _line(label, f"removed {removed} -> {ll}")
    except ListOpError as e:
        _line(label, f"error: {e}")


def _show_get(ll: DoublyLinkedList, label: str, pos: int) -> None:
    try:
        v = ll.get(pos)
        unit = "step" if ll.last_steps == 1 else "steps"
        end = "head" if ll.last_from_head else "tail"
        _line(label, f"{v}  ({ll.last_steps} {unit} from {end})")
    except ListOpError as e:
        _line(label, f"error: {e}")


def _show_search(ll: DoublyLinkedList, label: str, value: int) -> None:
    idx = ll.search(value)
    _line(label, f"found at index {idx}" if idx >= 0 else "not found")


def _show_walk(ll: DoublyLinkedList, label: str, forward: bool) -> None:
    values = []
    cur = ll.head if forward else ll.tail
    while cur is not None:
        values.append(str(cur.value))
        cur = cur.next if forward else cur.prev
    _line(label, " ".join(values))


def _show_check(ll: DoublyLinkedList, label: str) -> None:
    bad = ll.check()
    if bad == -2:
        _line(label, "ok")
    elif bad >= 0:
        _line(label, f"error: {CORRUPT} at index {bad}")
    else:
        _line(label, f"error: {CORRUPT}")


def demo() -> None:
    ll = DoublyLinkedList()

    print("=== Doubly linked list demo ===")
    _line("start", str(ll))

    _show(ll, "push_back 20", lambda: ll.push_back(20))
    _show(ll, "push_back 30", lambda: ll.push_back(30))
    _show(ll, "push_front 10", lambda: ll.push_front(10))
    _show(ll, "push_back 40", lambda: ll.push_back(40))
    _show(ll, "push_back 50", lambda: ll.push_back(50))

    _show_walk(ll, "forward", True)
    _show_walk(ll, "backward", False)

    _show_get(ll, "get at 1", 1)
    _show_get(ll, "get at 3", 3)
    _show_get(ll, "get at 9", 9)
    _show_search(ll, "search 30", 30)
    _show_search(ll, "search 77", 77)

    _show(ll, "insert 99 at 2", lambda: ll.insert(2, 99))
    _show(ll, "insert 5 at 0", lambda: ll.insert(0, 5))
    _show(ll, "insert 60 at end", lambda: ll.insert(ll.len, 60))
    _show(ll, "insert 7 at -1", lambda: ll.insert(-1, 7))

    _show_removed(ll, "pop_front", ll.pop_front)
    _show_removed(ll, "pop_back", ll.pop_back)
    _show_removed(ll, "delete at 2", lambda: ll.delete_at(2))
    _show(ll, "delete value 40", lambda: ll.delete_value(40))
    _show(ll, "delete value 77", lambda: ll.delete_value(77))

    held = ll.find(30)
    _line("hold node 30", "handle kept" if held is not None else "not found")
    _show_removed(ll, "remove held node", lambda: ll.remove_node(held))  # type: ignore[arg-type]

    ll.reverse()
    _line("reverse", str(ll))
    _show_walk(ll, "backward", False)
    _show_check(ll, "integrity check")

    victim = ll.head.next  # type: ignore[union-attr]  # holds 20
    saved_prev = victim.prev  # type: ignore[union-attr]
    victim.prev = victim  # type: ignore[union-attr]
    _line("corrupt node 20", "prev now points at itself")
    _show_check(ll, "integrity check")
    _show_removed(ll, "remove node 20", lambda: ll.remove_node(victim))  # type: ignore[arg-type]
    victim.prev = saved_prev  # type: ignore[union-attr]
    _line("repair node 20", "prev restored")
    _show_check(ll, "integrity check")

    ll.clear()
    _line("clear", str(ll))
    _show_removed(ll, "pop_front", ll.pop_front)
    _show_removed(ll, "pop_back", ll.pop_back)


# ---------------------------------------------------------------- benchmark

BUILD_N = 200_000
PASSES = 10
IDX_N = 20_000
IDX_GETS = 200
ROUNDS = 3


def bench() -> None:
    best_b = best_t = best_r = best_p = best_g = float("inf")
    sum_b = sum_t = sum_r = sum_p = sum_g = 0
    handles: list[Node] = [None] * BUILD_N  # type: ignore[list-item]

    for _ in range(ROUNDS):
        ll = DoublyLinkedList()

        t0 = time.perf_counter()
        for i in range(BUILD_N):
            handles[i] = ll.push_back(i)
        best_b = min(best_b, (time.perf_counter() - t0) * 1e3)
        sum_b = 0
        cur = ll.head
        while cur is not None:
            sum_b += cur.value
            cur = cur.next

        t0 = time.perf_counter()
        sum_t = 0
        for p in range(PASSES):
            if p % 2 == 0:
                cur = ll.head
                while cur is not None:
                    sum_t += cur.value
                    cur = cur.next
            else:
                cur = ll.tail
                while cur is not None:
                    sum_t += cur.value
                    cur = cur.prev
        best_t = min(best_t, (time.perf_counter() - t0) * 1e3)

        t0 = time.perf_counter()
        for i in range(0, BUILD_N, 2):
            ll.remove_node(handles[i])
        best_r = min(best_r, (time.perf_counter() - t0) * 1e3)
        sum_r = 0
        cur = ll.head
        while cur is not None:
            sum_r += cur.value
            cur = cur.next

        t0 = time.perf_counter()
        sum_p = 0
        step = 1
        while ll.len > 0:
            sum_p += step * ll.pop_back()
            step += 1
        best_p = min(best_p, (time.perf_counter() - t0) * 1e3)

        g = DoublyLinkedList()
        for i in range(IDX_N):
            g.push_back(i)
        t0 = time.perf_counter()
        sum_g = 0
        for k in range(IDX_GETS):
            sum_g += g.get((k * 97) % IDX_N)
        best_g = min(best_g, (time.perf_counter() - t0) * 1e3)
        g.clear()

    print(f"build_back    checksum={sum_b} time_ms={best_b:.3f}")
    print(f"traverse      checksum={sum_t} time_ms={best_t:.3f}")
    print(f"remove_held   checksum={sum_r} time_ms={best_r:.3f}")
    print(f"pop_back      checksum={sum_p} time_ms={best_p:.3f}")
    print(f"index_access  checksum={sum_g} time_ms={best_g:.3f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "bench":
        bench()
    else:
        demo()
