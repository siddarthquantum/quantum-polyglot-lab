# Array Lab (C)

Arrays are the first data structure in DSC512 and the base for everything after it: stacks, queues, hash tables and heaps are all built on arrays. In this lab you write the core array operations yourself and check them against shared tests.

| File | What it is |
| --- | --- |
| `array_ops.c` | **Your exercise file.** `main()` already reads the input. You fill in the ten functions marked `TODO`. |
| `solution/array_ops.c` | Reference answer. Open it only after your version passes, or when you're stuck for more than 15 minutes. |
| `tests/cases/` | `NAME.in` + `NAME.expected` must match exactly. `NAME.fail` means the input is malformed and the program must exit non-zero. |

## 1. Intuition

An array is one block of memory holding `n` values of the same type, side by side. If `a` starts at address `B` and each `int` takes 4 bytes, then

```text
address of a[i] = B + i × sizeof(int)
```

That one multiplication is why `a[i]` is **O(1)**, and why indices start at 0 (`a[0]` is at `B + 0`). It is also why inserting in the middle is **O(n)**: there is no gap to drop a value into, so everything after it must shift.

## 2. Operations and costs

| Operation | Time | Why |
| --- | --- | --- |
| Access `a[i]` | O(1) | Address arithmetic |
| Insert / delete at position | O(n) | Shift up to n elements |
| Linear search | O(n) | Might check every element |
| Binary search | O(log n) | Halves the range each step; needs sorted data |
| Insertion sort | O(n²), best O(n) | Fast on nearly sorted input |
| Reverse, rotate | O(n), O(1) extra space | Two-pointer swaps |

## 3. Exercises (do them in this order)

| # | Function | Tests that start passing |
| --- | --- | --- |
| 1 | `print_array` | `01_print`, `01_print_empty` |
| 2 | `insert_at` | `02_insert`, `02_insert_no_end` |
| 3 | `delete_at` | `03_delete` |
| 4 | `linear_search` | `04_search` |
| 5 | `is_sorted` | `05_bsearch_unsorted` |
| 6 | `binary_search` | `06_bsearch` |
| 7 | `insertion_sort` | `07_sort`, `07_sort_negatives` |
| 8 | `reverse_range` | `08_reverse_odd`, `08_reverse_even` |
| 9 | `rotate_left` | `09_rotate` |
| 10 | `find_max`, `find_min`, `sum_array` | `10_max_min_sum`, `11_empty_array`, `12_sum_no_overflow`, `13_overflow` |

Before coding each one, write its algorithm on paper in numbered steps, the way the lab exam asks. Then code from your steps.

## 4. Build and run (VS Code or Cursor)

Both editors work the same way, since Cursor is built on VS Code. Install the **C/C++** extension (Microsoft), open the repo folder, and use the built-in terminal (`` Ctrl+` ``):

```bash
# build (from the repo root)
gcc -std=c11 -Wall -Wextra -o array_ops c/array_lab/array_ops.c

# run all tests
c/array_lab/tests/run_tests.sh ./array_ops

# try one case by hand
./array_ops < c/array_lab/tests/cases/02_insert.in

# or type input yourself, then Ctrl+D to finish
./array_ops
```

To catch out-of-bounds bugs the way CI does, build with the sanitizers:

```bash
gcc -std=c11 -Wall -Wextra -Werror -g -fsanitize=address,undefined -o array_ops c/array_lab/array_ops.c
```

> **Exam tip:** the lab exam in VPL has no AI autocomplete. While practising, turn off Copilot in VS Code, or Cursor Tab in Cursor (Settings → Features), so your hands learn the code.

## 5. Input format

```text
5                 <- n (0..100)
10 20 30 40 50    <- the elements
INSERT 2 99       <- commands, one per line
PRINT
END
```

Commands: `PRINT`, `INSERT pos x`, `DELETE pos`, `SEARCH key`, `BSEARCH key`, `SORT`, `REVERSE`, `ROTATE k`, `MAX`, `MIN`, `SUM`, `END`.

Operation errors print a message and the program keeps going: `Overflow`, `Underflow`, `Invalid position`, `Array is empty`, `Array not sorted`. Malformed input (bad `n`, missing numbers, unknown command) prints to stderr and exits with code 1.

## 6. Edge cases the tests check

- Empty array (`n = 0`) for every operation
- Full array (`n = 100`) on insert
- Insert at `pos = n` (append) is valid; `pos = n + 1` is not
- Odd and even lengths for reverse
- Rotation by `k ≥ n`
- Sum of large values (needs `long long`)
- Negative numbers in sort and min

## 7. Security perspective

- **Bounds:** C never checks `a[i]`. Writing `a[100]` into `int a[100]` silently corrupts memory, which is a buffer overflow. Every index from input is checked before use (`pos`, `n`).
- **Integer overflow:** `low + high` can overflow for huge arrays, so binary search uses `low + (high - low) / 2`. Summing many `int`s can overflow, so the sum uses `long long`.
- **Input:** `scanf` return values are checked so a truncated input can't leave variables uninitialised.

## 8. Quick review

- `a[i]` is `*(a + i)`. The array name decays to a pointer to its first element.
- Inside a function, `int a[]` is really `int *a`, so `sizeof(a)` gives the pointer size, not the array size. That is why `n` is always passed in.
- Insert shifts right starting **from the end**. Delete shifts left starting **from pos**.
- Binary search needs sorted input.

## 9. Revision questions

1. Why is accessing `a[i]` O(1) but inserting at index 0 O(n)?
2. What goes wrong if `insert_at` shifts from left to right?
3. What does `sizeof(a) / sizeof(a[0])` give inside `main`, and inside a function that receives `a`?
4. Why does binary search fail on `5 1 4 2 3`?
5. How many comparisons does binary search need in the worst case for n = 100?
6. Why does rotating by `k` and by `k % n` give the same result?
7. Explain why three reversals rotate an array.
8. When is insertion sort faster than O(n²)?

## References

- Course slides: DSC512 *Data Structures* (arrays, analysis of array operations), Dr. Jisha Mariyam John, IIIT Kottayam.
- Horowitz, Sahni, Anderson-Freed, *Fundamentals of Data Structures in C*, ch. 2.
- Cormen et al., *Introduction to Algorithms*, 3rd ed., §2.1 (insertion sort).
