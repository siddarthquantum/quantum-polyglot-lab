"""Array basics in Python: traverse, insert, delete.

The array has a fixed CAPACITY (a pre-allocated list) and a SIZE (slots in use).
Every insert/delete keeps elements packed at indexes 0 .. size-1.

The shifting is written by hand on purpose so you can see the O(n) work.
In real Python code you would just use list.insert / list.pop, which do the
same shifting in C (see the extra "builtin" lines in the benchmark).

    python3 python/array_basics/array_basics.py         -> step-by-step demo
    python3 python/array_basics/array_basics.py bench   -> timing run
"""

import sys
import time


class ArrayOpError(Exception):
    """Raised for invalid operations (full, empty, bad position)."""


class FixedArray:
    def __init__(self, capacity: int) -> None:
        self.data = [0] * capacity  # Space O(capacity)
        self.size = 0
        self.capacity = capacity

    def __str__(self) -> str:
        # TRAVERSE: visit every element once. Time O(n), extra space O(n) for the string.
        return "[" + ", ".join(str(self.data[i]) for i in range(self.size)) + f"]  size={self.size}"

    def insert(self, pos: int, value: int) -> None:
        """Insert at pos (0 <= pos <= size). Time O(n) worst, O(1) at the end. Space O(1)."""
        if self.size == self.capacity:
            raise ArrayOpError("array is full")
        # Python would happily accept pos = -1 (it means "last element"),
        # so we must reject negative positions ourselves.
        if pos < 0 or pos > self.size:
            raise ArrayOpError("position out of range")
        for i in range(self.size, pos, -1):  # shift right, from the end
            self.data[i] = self.data[i - 1]
        self.data[pos] = value
        self.size += 1

    def delete(self, pos: int) -> int:
        """Delete and return element at pos (0 <= pos < size). Time O(n) worst. Space O(1)."""
        if self.size == 0:
            raise ArrayOpError("array is empty")
        if pos < 0 or pos >= self.size:
            raise ArrayOpError("position out of range")
        removed = self.data[pos]
        for i in range(pos, self.size - 1):  # shift left to close the gap
            self.data[i] = self.data[i + 1]
        self.size -= 1
        return removed


# --------------------------------------------------------------------- demo


def label(text: str) -> str:
    return f"{text:<17}: "


def show_insert(a: FixedArray, text: str, pos: int, value: int) -> None:
    try:
        a.insert(pos, value)
        print(label(text) + str(a))
    except ArrayOpError as e:
        print(label(text) + f"error: {e}")


def show_delete(a: FixedArray, text: str, pos: int) -> None:
    try:
        removed = a.delete(pos)
        print(label(text) + f"removed {removed} -> {a}")
    except ArrayOpError as e:
        print(label(text) + f"error: {e}")


def demo() -> None:
    a = FixedArray(8)
    for v in (10, 20, 30, 40, 50):
        a.insert(a.size, v)

    print(f"=== Array basics demo (capacity {a.capacity}) ===")
    print(label("start") + str(a))
    print(label("traverse") + " ".join(str(a.data[i]) for i in range(a.size)))
    print(label("access a[3]") + str(a.data[3]))

    show_insert(a, "insert 99 at 2", 2, 99)
    show_insert(a, "insert 5 at 0", 0, 5)
    show_insert(a, "insert 60 at end", a.size, 60)
    show_insert(a, "insert 1 at 0", 0, 1)  # full
    show_delete(a, "delete at 3", 3)
    show_delete(a, "delete at 0", 0)
    show_delete(a, "delete at end", a.size - 1)
    show_delete(a, "delete at 9", 9)  # out of range
    show_insert(a, "insert 7 at -1", -1, 7)  # negative index


# ---------------------------------------------------------------- benchmark

TRAVERSE_N = 1_000_000
TRAVERSE_PASSES = 10
SHIFT_K = 5_000
ROUNDS = 3


def ms_since(t0: int) -> float:
    return (time.perf_counter_ns() - t0) / 1e6


def bench() -> None:
    best_t = best_i = best_d = best_bi = best_bd = float("inf")
    sum_t = sum_i = sum_d = 0

    for _ in range(ROUNDS):
        a = FixedArray(TRAVERSE_N)
        for i in range(TRAVERSE_N):
            a.insert(a.size, i)

        t0 = time.perf_counter_ns()
        sum_t = 0
        for _ in range(TRAVERSE_PASSES):
            for i in range(a.size):
                sum_t += a.data[i]
        best_t = min(best_t, ms_since(t0))

        a = FixedArray(SHIFT_K)
        t0 = time.perf_counter_ns()
        for i in range(SHIFT_K):
            a.insert(0, i)  # worst case
        best_i = min(best_i, ms_since(t0))
        sum_i = sum(j * a.data[j] for j in range(a.size))

        t0 = time.perf_counter_ns()
        sum_d = 0
        step = 1
        while a.size > 0:
            sum_d += step * a.delete(0)  # worst case
            step += 1
        best_d = min(best_d, ms_since(t0))

        # Same work using Python's built-in list (shifting is done in C by memmove).
        b: list[int] = []
        t0 = time.perf_counter_ns()
        for i in range(SHIFT_K):
            b.insert(0, i)
        best_bi = min(best_bi, ms_since(t0))
        t0 = time.perf_counter_ns()
        while b:
            b.pop(0)
        best_bd = min(best_bd, ms_since(t0))

    print(f"traverse      checksum={sum_t} time_ms={best_t:.3f}")
    print(f"insert_front  checksum={sum_i} time_ms={best_i:.3f}")
    print(f"delete_front  checksum={sum_d} time_ms={best_d:.3f}")
    print(f"insert_front_builtin_list.insert time_ms={best_bi:.3f}")
    print(f"delete_front_builtin_list.pop(0) time_ms={best_bd:.3f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "bench":
        bench()
    else:
        demo()
