# Array Basics in Four Languages: Traverse, Insert, Delete

**Start here if this is your first time with data structures.** One idea (the array), three operations, four languages, and a measured answer to two questions: *which language is fastest?* and *which is safest?*

| Language | File |
| --- | --- |
| C | [`c/array_basics/array_basics.c`](../../c/array_basics/array_basics.c) |
| Java | [`java/array_basics/ArrayBasics.java`](../../java/array_basics/ArrayBasics.java) |
| Python | [`python/array_basics/array_basics.py`](../../python/array_basics/array_basics.py) |
| Rust | [`rust/array_basics/array_basics.rs`](../../rust/array_basics/array_basics.rs) |
| Shared | `expected_demo.txt` (all four must print this exactly) and `run_all.sh` (build, check, benchmark) |

```bash
shared/array_basics/run_all.sh          # build all 4, check identical output, run Rust unit tests
shared/array_basics/run_all.sh bench    # ...plus the speed comparison
```

---

## 1. What is an array?

Think of a row of numbered lockers in a school corridor. Every locker is the same size, they sit side by side, and numbering starts at **0**.

```text
index:     0    1    2    3    4    5    6    7
         ┌────┬────┬────┬────┬────┬────┬────┬────┐
value:   │ 10 │ 20 │ 30 │ 40 │ 50 │    │    │    │
         └────┴────┴────┴────┴────┴────┴────┴────┘
          ◄──────── size = 5 ────────►
          ◄──────────────── capacity = 8 ──────────────►
```

- **capacity**: how many lockers exist (fixed when the array is created).
- **size**: how many are in use. Used lockers are always packed at the left, with no gaps.

Because every slot is the same size and they are side by side, the computer finds slot `i` with one calculation:

```text
address of a[i] = start address + i × (size of one element)
```

That is why reading `a[3]` takes the same time whether the array has 5 elements or 5 million. It is also why indexes start at 0: `a[0]` is at `start + 0`.

---

## 2. The three operations

### Traverse: visit every element once

```text
for i from 0 to size-1:
    look at a[i]
```

You touch each of the `n` elements once, so the work grows in step with `n`.

### Insert at position `pos`

There is no empty space in the middle, so you **make room** by sliding everything from `pos` onwards one step to the right. Insert 99 at position 2:

```text
before:  [10, 20, 30, 40, 50, __ ]
step 1:  [10, 20, 30, 40, 50, 50 ]   a[5] = a[4]
step 2:  [10, 20, 30, 40, 40, 50 ]   a[4] = a[3]
step 3:  [10, 20, 30, 30, 40, 50 ]   a[3] = a[2]
place:   [10, 20, 99, 30, 40, 50 ]   a[2] = 99, size = 6
```

**Shift from the right end.** If you go left to right, `a[3] = a[2]` overwrites 40 before you have copied it, and you get `[10, 20, 30, 30, 30, 30]`. This is the most common beginner bug.

Two checks come first: is the array **full**? Is `pos` between `0` and `size`?

### Delete at position `pos`

Slide everything after `pos` one step to the **left** to close the gap. Delete position 1 from `[10, 20, 30, 40]`:

```text
before:  [10, 20, 30, 40]
step 1:  [10, 30, 30, 40]   a[1] = a[2]
step 2:  [10, 30, 40, 40]   a[2] = a[3]
done:    [10, 30, 40]       size = 3  (the old 40 at index 3 is now outside size, so it's ignored)
```

Here you shift **left to right**, the opposite of insert. Check first: is the array **empty**? Is `0 <= pos < size`?

---

## 3. Asymptotic notation (Big-O, Big-Ω, Big-Θ)

We don't measure algorithms in seconds, because seconds depend on the laptop. We count **how the number of steps grows as the input size `n` grows**, and ignore constants (`3n + 5` is just "grows like `n`").

| Notation | Read as | Meaning | Analogy |
| --- | --- | --- | --- |
| **O(f(n))** | "Big-O" | Upper bound: never grows **faster** than f(n) | "The trip takes **at most** 2 hours" |
| **Ω(f(n))** | "Big-Omega" | Lower bound: never grows **slower** than f(n) | "The trip takes **at least** 30 minutes" |
| **Θ(f(n))** | "Big-Theta" | Tight bound: grows **exactly** like f(n) | "The trip takes about 1 hour" |

Formally: `f(n) = O(g(n))` if there are constants `c > 0` and `n₀` such that `f(n) ≤ c·g(n)` for all `n ≥ n₀`. Ω flips `≤` to `≥`, and Θ means both hold.

The common growth rates, from fastest to slowest for large `n`:

```text
O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2ⁿ)
```

In interviews, "what's the complexity?" means **worst-case Big-O** unless they say otherwise.

**Best, average and worst case** are separate questions from O/Ω/Θ. For insert:
- best case: `pos = size` (append), 0 shifts.
- worst case: `pos = 0`, all `n` elements shift.
- average case: random `pos`, about `n/2` shifts, which is still **Θ(n)** because we drop the `½`.

---

## 4. Complexity table (memorise this)

`n` = number of elements currently stored (`size`).

| Operation | Best case | Worst case | Average | Extra space | Why |
| --- | --- | --- | --- | --- | --- |
| Access `a[i]` | Θ(1) | Θ(1) | Θ(1) | O(1) | One address calculation |
| Traverse | Θ(n) | Θ(n) | Θ(n) | O(1) | Visit each element once |
| Insert at end (`pos = size`) | Θ(1) | Θ(1) | Θ(1) | O(1) | Nothing to shift |
| Insert at `pos` | Θ(1) | **Θ(n)** (`pos = 0`) | Θ(n) | O(1) | Shift `size - pos` elements right |
| Delete at end | Θ(1) | Θ(1) | Θ(1) | O(1) | Nothing to shift |
| Delete at `pos` | Θ(1) | **Θ(n)** (`pos = 0`) | Θ(n) | O(1) | Shift `size - pos - 1` elements left |
| Search (unsorted) | Θ(1) | Θ(n) | Θ(n) | O(1) | May have to traverse everything |

**Space for the array itself is Θ(capacity).** "Extra space O(1)" means each operation only needs a few loop variables, no second array: it works **in place**.

> **Interview follow-up you will be asked:** "How does Python's `list` / Java's `ArrayList` / Rust's `Vec` append in O(1) if the array is full?" They allocate a new array about 1.5–2× bigger and copy everything over. That one copy is O(n), but it happens so rarely that the **amortized** cost per append is O(1).

---

## 5. Same algorithm, four languages

The algorithm is identical in all four files; only the language changes. What differs is how each language handles mistakes.

| What happens if... | C | Java | Python | Rust |
| --- | --- | --- | --- | --- |
| you read `a[10]` on an 8-slot array | **Undefined behaviour**: reads whatever memory is there, or crashes, or silently corrupts data | `ArrayIndexOutOfBoundsException` | `IndexError` | panic (clean stop with a message), or `a.get(10)` returns `None` |
| you use index `-1` | Reads memory **before** the array (UB) | Exception | **No error**: `-1` means "last element", which can hide bugs | Won't compile: indexes are `usize` (never negative). User input needs an explicit `usize::try_from(-1)`, which returns an error |
| you forget to free memory | Memory leak | Garbage collector frees it | Garbage collector frees it | Freed automatically when the owner goes out of scope (no GC needed) |
| you use memory after freeing it | Use-after-free (UB, a top security bug) | Impossible | Impossible | **Compile error** (borrow checker) |
| you ignore an error | Easy: return codes can be ignored | Checked exceptions must be caught or declared | Easy: exceptions go unnoticed until runtime | `Result` must be handled; the compiler warns if you ignore it |
| an `int` overflows | Signed overflow is UB | Wraps around silently | Never overflows (big integers) | Panics in debug builds, wraps in release |

Notice in the C file that `array_insert` checks `pos < 0 || pos > a->size` **by hand**. In C, nobody else checks it for you. Remove that line and run `./array_basics_c_asan`: AddressSanitizer will report a buffer overflow. Without the sanitizer the program may run "fine" while corrupting memory, and buffer overflows like that are how many real-world exploits work.

---

## 6. Which is faster? (measured, not guessed)

`run_all.sh bench` runs the same workload in each language, best of 3 rounds. All four print the **same checksums**, which shows they did the same work.

- **traverse**: sum 1,000,000 ints, 10 passes (10 million reads)
- **insert_front**: insert 5,000 values, each at index 0 (worst case, ~12.5 million shifts)
- **delete_front**: delete them all from index 0 (worst case)

Measured on a 4-core Intel Xeon cloud VM (GCC 13 `-O2`, OpenJDK, CPython 3.13, rustc 1.97 `-O`), two runs, typical values:

| Workload | C | Rust | Java | Python (hand loop) | Python (built-in `list`) |
| --- | --- | --- | --- | --- | --- |
| traverse | 3.1 ms | **2.1–2.5 ms** | 11–16 ms | 270 ms | n/a |
| insert_front | **0.28 ms** | 10.0 ms (0.28 ms with `copy_within`) | 2.0 ms | 335 ms | 1.5 ms |
| delete_front | 4.5 ms | 4.4 ms | **1.7 ms** | 340 ms | 22 ms |

Your numbers will differ by machine. The **ratios** are what matter.

### What the numbers teach

1. **C and Rust are in the same class.** Both compile to native machine code. Neither is consistently ahead: Rust won traverse, C won insert.
2. **Why Rust's insert was 35× slower than C's:** Rust checks `self.data[i]` against the bounds on every access. In the backwards shift loop, those checks stopped the compiler from turning the loop into a single fast block copy (`memmove`), which GCC did for C. Replacing the loop with `self.data.copy_within(pos..self.size, pos + 1)` (see the comment in the Rust file) brought it to **0.28 ms, the same as C**. Lesson: in Rust, use the slice methods (`copy_within`, iterators). They are both safe and fast.
3. **Java is close behind** and sometimes ahead (delete). The JIT compiler turns hot loops into machine code while the program runs. Java pays a little for start-up and bounds checks.
4. **Python's hand-written loop is ~100× slower.** Every `a[i] = a[i-1]` is interpreted bytecode working on boxed integer objects. But `list.insert(0, x)`, which runs the same algorithm in C inside CPython, is **~200× faster** than the hand loop. **In Python, use the built-ins.**
5. **Big-O beats language choice.** O(n) insert at the front of a big array is slow in *every* language. If you insert at the front often, change the data structure (`collections.deque`, `ArrayDeque`, `VecDeque`: O(1) at both ends). Picking the right structure gains more than switching languages.

### Overall ranking

| Rank | Speed (for this workload) | Memory safety |
| --- | --- | --- |
| 1 | **C ≈ Rust** (native code) | **Rust**: checked at compile time *and* at run time, with no garbage collector |
| 2 | **Java** (JIT, within a few × of native) | **Java ≈ Python**: bounds checks and a garbage collector. Python's `-1` indexing and dynamic types let some bugs through |
| 3 | **Python** (interpreted; fast only through C-backed built-ins) | **C**: no checks. Safety depends entirely on the programmer, plus tools like ASan, Valgrind and static analysis |

**One-line answer for an interview:**
> "C and Rust are fastest because both compile to native code. Rust adds memory safety at compile time with almost no runtime cost, so for new systems code where security matters, Rust is the safer choice. Java trades a little speed for a managed runtime. Python is slowest for hand-written loops but fast when you use its C-backed built-ins. Algorithm choice (Big-O) matters more than language choice."

---

## 7. Common mistakes checklist

- [ ] Shifting the wrong way during insert (must go **right to left**)
- [ ] Forgetting the **full** check before insert, or the **empty** check before delete
- [ ] Off-by-one: insert allows `pos == size` (append); delete allows only `pos <= size - 1`
- [ ] Forgetting `size++` / `size--`
- [ ] Python: accepting negative positions because `a[-1]` "works"
- [ ] C: `free()` without setting the pointer to `NULL` (dangling pointer)

## 8. Revision questions (answer without looking)

1. Why is `a[i]` O(1) but insert at index 0 O(n)?
2. What breaks if insert shifts left-to-right? Show it on `[1, 2, 3]` inserting 9 at index 0.
3. What is the difference between O(n), Ω(n) and Θ(n)? Give the best and worst case of delete.
4. What is the extra space of insert, and why is it not O(n)?
5. In which language does `a[-1]` silently succeed, and why is that risky?
6. Why was Rust's hand loop slower than C's here, and how was it fixed?
7. How does a dynamic array give O(1) amortized append?

## 9. Quick review

```text
Problem         : traverse, insert, delete on a fixed-capacity array
Idea            : contiguous memory + address arithmetic
Time            : access O(1), traverse Θ(n), insert/delete O(n) worst, O(1) at end
Space           : Θ(capacity) storage, O(1) extra per operation (in place)
Key difference  : C has no bounds checks; Java/Python check at run time; Rust checks at compile time + run time
Security        : unchecked index = buffer overflow = classic exploit
Takeaway        : choose the right data structure first, then the language
```

## 10. References

- Cormen, Leiserson, Rivest, Stein: *Introduction to Algorithms*, 4th ed., ch. 3 (asymptotic notation) and ch. 10 (elementary data structures).
- Kernighan & Ritchie: *The C Programming Language*, 2nd ed., ch. 5 (pointers and arrays).
- *The Rust Programming Language*, ch. 4 (ownership) and ch. 8 (vectors): <https://doc.rust-lang.org/book/>
- Java Language Specification §10 (arrays): <https://docs.oracle.com/javase/specs/>
- Python docs, time complexity of `list` operations: <https://wiki.python.org/moin/TimeComplexity>
- MITRE CWE-787 (out-of-bounds write) and CWE-125 (out-of-bounds read).
