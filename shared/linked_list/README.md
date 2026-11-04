# Linked Lists in Four Languages: Traverse, Insert, Delete, Reverse, Cycle Detection

**Read `shared/array_basics/README.md` first.** This problem is the direct sequel: the array taught you that contiguous memory gives O(1) access but O(n) insertion. The linked list makes the opposite trade, and understanding *why* is the point of the exercise.

| Language | File |
| --- | --- |
| C | [`c/linked_list/linked_list.c`](../../c/linked_list/linked_list.c) |
| Java | [`java/linked_list/LinkedListLab.java`](../../java/linked_list/LinkedListLab.java) |
| Python | [`python/linked_list/linked_list.py`](../../python/linked_list/linked_list.py) |
| Rust | [`rust/linked_list/linked_list.rs`](../../rust/linked_list/linked_list.rs) |
| Shared | `expected_demo.txt` (all four must print this exactly) and `run_all.sh` (build, check, benchmark) |

```bash
shared/linked_list/run_all.sh          # build all 4, check identical output, ASan leak check, Rust unit tests
shared/linked_list/run_all.sh bench    # ...plus the speed comparison
```

`run_all.sh` enforces three things: all four print byte-identical demo output, the C build is clean under AddressSanitizer and UndefinedBehaviorSanitizer (including no leaks), and **all four produce identical benchmark checksums**, which proves they really did the same work rather than merely finishing.

---

## 1. What is a linked list?

An array is a row of numbered lockers, side by side. A linked list is a **treasure hunt**: each node holds a value and the address of the next node. The nodes can be anywhere in memory.

```text
head
 │
 ▼
┌──────┬───┐   ┌──────┬───┐   ┌──────┬───┐
│  10  │ ●─┼──▶│  20  │ ●─┼──▶│  30  │ / │
└──────┴───┘   └──────┴───┘   └──────┴───┘
  value next     value next     value next        / = NULL / None / None
```

Two consequences follow from this picture, and almost everything else is a corollary:

1. **There is no address arithmetic.** To reach index `i` you must start at `head` and follow `i` pointers. Access is **O(n)**, not O(1).
2. **Splicing is local.** To insert between two nodes you change two pointers. Nothing shifts. Once you are *holding the right node*, insertion and deletion are **O(1)**.

### The operation that defines the structure

Insert 99 after the node holding 10:

```text
before:  [10|●]──▶[20|●]──▶[30|/]

step 1:  new node points at 20      [99|●]──▶[20|●]
step 2:  node 10 points at 99       [10|●]──▶[99|●]──▶[20|●]──▶[30|/]
```

**Order matters absolutely.** Do step 2 first and the only pointer to node 20 is gone: the rest of the list is leaked in C, garbage-collected in Java/Python, and rejected by the compiler in Rust. This is the linked-list equivalent of the array's "shift from the wrong end" bug.

Deletion is the mirror image: make the previous node point past the victim, then free the victim (C) or let it be collected (Java/Python) or dropped (Rust).

```text
delete 20:   [10|●]────────▶[30|/]
                    [20|●]  ← unlinked; now unreachable
```

---

## 2. Why keep a `len` field?

All four implementations store the length rather than counting nodes each time. Counting is O(n); storing is O(1) with one integer of bookkeeping per list. The cost is a classic correctness risk: **every mutation must update it**. A `len` that drifts out of sync is worse than no `len`, because `get`'s bounds check then trusts a lie. If you add an operation to these files, the `len++` / `len--` is part of the operation, not an afterthought.

---

## 3. Complexity: the whole point of the exercise

`n` = number of nodes. "Holding the node" means you already have a pointer to it, as you do while traversing.

| Operation | Linked list | Array | Why |
| --- | --- | --- | --- |
| Access / `get(i)` | **Θ(n)** | **Θ(1)** | List: walk `i` pointers. Array: one address calculation |
| Traverse all | Θ(n) | Θ(n) | Same Big-O, **very** different constant (see §5) |
| Insert at head | **Θ(1)** | **Θ(n)** | List: two pointer writes. Array: shift everything right |
| Insert at tail | Θ(n)¹ | Θ(1) | List: walk to the end first. Array: write at `size` |
| Insert while holding the node | **Θ(1)** | Θ(n) | List: splice. Array: still has to shift |
| Delete at head | **Θ(1)** | Θ(n) | Mirror of insert |
| Delete while holding the node | Θ(1)² | Θ(n) | ²singly linked needs the *previous* node, so Θ(n) to find it |
| Search by value | Θ(n) | Θ(n) | Both must look at everything |
| Reverse | Θ(n), O(1) extra | Θ(n), O(1) extra | Flip pointers vs swap ends |
| Find middle | Θ(n), O(1) extra | Θ(1) | List: two-pointer walk. Array: `a[size/2]` |
| Memory per element | value + pointer | value | **4× here** (see §5) |

¹ Θ(1) if you also keep a `tail` pointer. These files deliberately do not, so that `push_back` visibly costs a walk. A production list (Java's `java.util.LinkedList`, Rust's `std::collections::LinkedList`) keeps `tail` *and* back-pointers, making it doubly linked with O(1) at both ends.

² This is the single most common linked-list interview trap. In a **singly** linked list, "delete this node" is O(n) because you need its predecessor. The famous trick when you are given *only* the victim and it is not the last node: copy the next node's value into the victim and delete the *next* node instead, in O(1).

### Best, worst, average

For `insert(pos)` and `delete_at(pos)`:
- best case: `pos = 0`, **Θ(1)**, no walk.
- worst case: `pos = len`, **Θ(n)**, walk the whole list.
- average over random `pos`: about `n/2` steps, still **Θ(n)**.

Note the asymmetry with arrays: for an array, `pos = 0` is the *worst* case and `pos = size` is the best. The two structures are worst-case opposites, which is exactly why "which is better?" has no answer without a workload.

---

## 4. Beyond the basics: the three algorithms that get asked

These are in all four files because they appear constantly in interviews, and because each teaches a reusable technique.

### Reverse (pointer flipping)

```text
prev=/   cur=[1]──▶[2]──▶[3]
         save next, flip cur, advance both
result:  /◀──[1]◀──[2]◀──[3]   head=3
```

Three pointers (`prev`, `cur`, `next`) and one rule: **save `next` before overwriting `cur.next`**. O(n) time, O(1) space.

### Middle (tortoise and hare)

`fast` takes two steps for every one of `slow`. When `fast` runs off the end, `slow` is at the middle — in **one pass**, without knowing the length.

```text
[1]──[2]──[3]──[4]──[5]
 s,f
      s         f
           s         f → off the end, slow = middle = 3
```

For an even length these files return the **second** of the two middles. That is a convention, not a law; state which one you mean when asked.

### Cycle detection (Floyd's algorithm)

If a `next` pointer loops backwards, the list has no end and every loop in this file would spin forever. Floyd's: run the same two pointers; in a cycle the hare gains one step per iteration on the tortoise, so it must eventually land on it.

```text
[1]──▶[2]──▶[3]──▶[4]
             ▲      │
             └──────┘      slow and fast meet inside the loop
```

O(n) time, **O(1) extra space** — this is why it beats the obvious "keep a set of visited nodes", which is O(n) space.

---

## 5. Measured: linked list vs array, same machine, same `n`

Big-O says traverse is Θ(n) for both. Reality says otherwise, and the gap is the most practically useful thing on this page. Fair head-to-head in C (`-O2`, n = 50,000, two runs):

| Operation | Array | Linked list | Winner |
| --- | --- | --- | --- |
| insert at front, 50,000× | 84–109 ms | **2.0–4.8 ms** | **list, ~20–40× faster** |
| `get(i)`, 2,000 random indexes | **0.013–0.040 ms** | 135–138 ms | **array, ~3,000–10,000× faster** |
| traverse, 10 passes | **0.12 ms** | 1.04–1.10 ms | **array, ~9× faster** |
| memory for 50,000 `int`s | **200 KB** | 800 KB | **array, 4× smaller** |

Three lessons, and they are the ones that matter:

1. **The O(1)-vs-O(n) insert advantage is real and large.** This is the reason linked lists exist.
2. **The O(n) access penalty is catastrophic, not academic.** Three to four orders of magnitude. If your code indexes into a list in a loop, you have written an accidental O(n²) algorithm.
3. **Equal Big-O ≠ equal speed.** Traversal is Θ(n) for both, yet the array is ~9× faster. An array walk reads consecutive bytes, so the CPU prefetches whole cache lines ahead; a list walk jumps to wherever `malloc` put each node, and each jump risks a cache miss the prefetcher cannot predict. **Big-O counts operations; it does not count cache misses.** The 4× memory overhead (on x86-64 a `{int, pointer}` node is 16 bytes — 4 for the `int`, 4 wasted on alignment padding, 8 for the pointer — versus 4 for a bare `int`) makes the misses more likely still.

> **The honest conclusion, and a good interview answer:** for most real workloads on modern hardware, a dynamic array (`Vec`, `ArrayList`, `list`) beats a linked list even where Big-O suggests it should not, because cache locality dominates. Reach for a linked list when you need O(1) splicing at a position you are **already holding** — an LRU cache's intrusive list, a free list in an allocator, an adjacency list for a graph. Reach for a deque (`collections.deque`, `ArrayDeque`, `VecDeque`) when you merely need fast push/pop at both ends: those are array-backed and keep the locality.

---

## 6. Measured: the same list across four languages

`run_all.sh bench`, best of 3 rounds, two separate runs. 200,000 nodes for `build_front`/`traverse`/`pop_front`; 200 `get(i)` calls on 20,000 nodes for `index_access`. All four print the **same checksums**, which is what makes the comparison meaningful.

Measured on a 4-core cloud VM (GCC `-O2`, OpenJDK 21, CPython 3.13, rustc `-O`):

| Workload | C | Rust | Java | Python |
| --- | --- | --- | --- | --- |
| build_front (200k pushes) | **1.88–1.92 ms** | 2.41–2.59 ms | 2.95–2.99 ms | 83–85 ms |
| traverse (10 passes) | 6.18–7.15 ms | 5.06–6.73 ms | **3.86–4.43 ms** | 97–101 ms |
| index_access (200 gets) | 4.69–4.73 ms | 4.05–4.85 ms | **2.59–2.60 ms** | 49–54 ms |
| pop_front (200k pops) | 2.42–2.52 ms | 3.51–4.38 ms | **1.20–1.24 ms** | 60–74 ms |

Your numbers will differ by machine; the **ratios** are what matter.

### What the numbers teach

1. **C, Rust and Java are all within ~2× of each other.** The gaps here are far smaller than in the array problem, because this workload is dominated by *memory latency* (chasing pointers) and *allocation*, not by arithmetic the compiler can optimise. When you are waiting on cache misses, it matters less which compiler produced the instructions.
2. **Java often wins the pointer-chasing workloads.** Two reasons, both worth knowing: its generational allocator is a pointer bump, so allocating 200k short-lived nodes is cheaper than 200k `malloc` calls; and nodes allocated consecutively tend to land consecutively, which a copying collector then keeps compact. Java's weakness in the array problem (bounds checks on tight numeric loops) simply does not bite here.
3. **Rust pays a small, visible cost on `pop_front`.** `delete_at(0)` does `Option::take()` twice (move the head out, move its `next` back in) where C does two raw pointer assignments. That is the price of making use-after-free unrepresentable, and ~1 ms per 200,000 operations is a fair exchange.
4. **Python is ~30–40× slower**, better than the ~100× of the array problem. The reason is instructive: here *every* language pays for allocation and pointer chasing, so Python's interpreter overhead is a smaller share of the total. Note too that each Python node is a full object; `__slots__` (used in our `Node`) removes the per-instance `__dict__` and is the single biggest win available. In real code you would use `collections.deque`, which is a C-implemented doubly linked list of *blocks* and beats this hand-written version by a wide margin.
5. **Big-O still beats language choice.** Python's `index_access` is ~50 ms and C's is ~4.7 ms — about 10×. But switching from a list to an array for that same operation is a ~3,000× win *in the same language*. **Pick the structure first, then the language.**

---

## 7. Same algorithm, four memory models

This is where the linked list earns its place in a four-language lab: it is the smallest data structure that forces each language to show you its real memory model.

| Concern | C | Java | Python | Rust |
| --- | --- | --- | --- | --- |
| "no next node" | `NULL` pointer | `null` reference | `None` | `Option::None` — **no null exists** |
| Who frees a deleted node | **You.** `free(victim)` | Garbage collector, eventually | Refcount hits zero, freed at once | Owner goes out of scope; freed deterministically |
| Forget to free | **Memory leak** | Impossible | Impossible | Impossible |
| Use a node after deleting it | **Use-after-free (UB)** — a top-tier exploit primitive | Impossible | Impossible | **Compile error** (borrow checker) |
| Free the same node twice | **Double free (UB)** | Impossible | Impossible | Impossible — ownership is unique |
| Forget a NULL check | Segfault, or silent corruption | `NullPointerException` | `AttributeError` | **Will not compile**: you must unwrap the `Option` |
| Lose the only pointer to the tail | Leaked silently | Collected | Collected | Caught at compile time |
| Can you build a cycle? | Yes, trivially | Yes, trivially | Yes, trivially | **No** — see below |
| Cost of deleting the list | O(n) frees you must write | O(1) for you | O(n) refcount drops | O(n) drops, automatic |

### The Rust lesson: a cycle is unrepresentable

In Rust a node is `Option<Box<Node>>`. `Box` is **unique ownership**: exactly one owner, freed when that owner dies. A cycle needs node 3 to point back at node 1, which would make node 1 owned twice. `cur.next = earlier_node;` **does not compile**.

So `has_cycle()` in the Rust file always returns `false`, and that is not a bug — it is the type system deleting an entire bug class. Building a real cycle in safe Rust requires `Rc<RefCell<Node>>` (shared ownership with runtime checks), and the result is then a **memory leak**, because the reference counts never reach zero. Rust converts a crash into a leak; `Weak` references are the fix.

Compare with C, where a single mistyped assignment creates a cycle, `list_clear` then loops forever freeing the same nodes, and `len` becomes a lie. Our C file ships `list_has_cycle` precisely because C gives you nothing else.

> **This is the headline comparison for teaching:** the same twenty-line algorithm is *routine* in Java and Python, *dangerous* in C, and *hard to write but impossible to get wrong* in Rust. The difficulty you feel writing the Rust version is the compiler front-loading the debugging you would otherwise do later, with a sanitizer, on a Friday night.

### The Rust footgun worth knowing

The automatic `Drop` for a `Box` chain is **recursive** — one stack frame per node. Measured on this machine, dropping a list without an iterative `clear()` overflows the stack at **200,000 nodes in a debug build** and **1,000,000 in a release build**. That is why the Rust file implements `Drop` by calling an iterative `clear()`, and why `std::collections::LinkedList` uses raw pointers internally rather than a `Box` chain. A safe abstraction is not automatically a *carefree* one.

### The C lesson, concretely

Run the ASan build and the leak checker is watching:

```bash
gcc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined \
    -o linked_list_asan c/linked_list/linked_list.c
./linked_list_asan
```

Now delete the `free(victim);` line in `list_delete_at` and run it again: AddressSanitizer reports the leaked bytes and the exact allocation stack. Or move `free(cur)` *above* `Node *next = cur->next;` in `list_clear` and you get a textbook **use-after-free** report. Both mistakes are two characters away from correct code, and neither is possible in the other three languages.

---

## 8. Security perspective

Linked lists are not an academic curiosity in security: heap exploitation is largely the art of corrupting them.

- **Use-after-free (CWE-416).** Freeing a node while another pointer still refers to it. Attackers reclaim that memory with controlled data and the stale pointer now reads attacker-chosen bytes. The `victim->next = NULL` before freeing, and setting pointers to `NULL` after `free`, are cheap habits that turn silent corruption into an immediate crash.
- **Double free (CWE-415).** Freeing the same node twice corrupts the allocator's own free lists — which are themselves linked lists. "Unlink" exploits against glibc are the classic worked example.
- **Memory leak / resource exhaustion (CWE-401).** A list that grows on untrusted input and never frees is a denial-of-service. Bound the length when the input is not yours.
- **Infinite loop on a corrupted list (CWE-835).** A cycle turns every traversal into a hang. Run `has_cycle` as a guard when a structure crosses a trust boundary.
- **NULL dereference (CWE-476).** The empty-list and end-of-list checks in these files are not ceremony.
- **Integer issues in `len`.** We use a signed `long` in C and reject negative positions explicitly. Rust's `usize` plus the explicit `to_index` conversion makes a negative index a compile-time-typed error rather than a runtime surprise.

The through-line: **C requires you to be correct; Rust requires you to prove it; Java and Python make the memory errors impossible but let logic errors (a wrong `len`, a lost tail) through just as easily.** No language saves you from a wrong algorithm.

---

## 9. Common mistakes checklist

- [ ] Relinking in the wrong order on insert (point the **new node** at the rest **first**)
- [ ] Not saving `next` before overwriting `cur->next` in `reverse` or `clear`
- [ ] Forgetting that a singly linked list needs the **previous** node to delete a node
- [ ] Forgetting `len++` / `len--`, so the bounds checks start trusting a wrong length
- [ ] Off-by-one: `insert` allows `pos == len` (append); `delete_at` allows only `pos <= len - 1`
- [ ] C: `free`ing the victim before reading `victim->value` or `victim->next`
- [ ] C: losing the head pointer and leaking the entire list
- [ ] Python: accepting a negative position because `-1` "works" on real sequences
- [ ] Rust: the default recursive `Drop` on a long list (use an iterative `clear`)
- [ ] Indexing a linked list inside a loop and quietly writing an O(n²) algorithm

## 10. Revision questions (answer without looking)

1. Why is `get(i)` O(n) on a list but O(1) on an array? What in the memory layout causes it?
2. Insert 99 at the head of `[10, 20]`. Write the two pointer assignments in the correct order, then explain what breaks if you swap them.
3. A singly linked list is Θ(1) to delete at the head but Θ(n) to delete a node you are holding. Why? What is the O(1) trick, and when does it fail?
4. Traverse is Θ(n) for both an array and a list, yet the array measured ~9× faster. Explain, using the words *cache line* and *prefetch*.
5. Describe Floyd's cycle detection and state its time and space complexity. Why is it preferred over a visited-set?
6. Why does `has_cycle()` always return `false` in the Rust implementation? What would you need to build a cycle in safe Rust, and what goes wrong then?
7. Which language won `pop_front` in the benchmark, and what about its memory allocator explains that?
8. Name three CWEs that arise from mishandling linked-list nodes in C, and the line of code in our file that prevents each.
9. When would you genuinely choose a linked list over a dynamic array in production?
10. For an even-length list, which of the two middle nodes does our `middle()` return, and how would you change it to return the other?

## 11. Quick review

```text
Problem         : traverse, insert, delete, search, reverse, middle, cycle detect on a singly linked list
Idea            : each node stores a value plus the address of the next node
Time            : access/search O(n); insert/delete O(1) at head, O(n) at position; reverse/middle/cycle O(n)
Space           : O(n) nodes, O(1) extra per operation; ~4x an array's bytes for int data
Key difference  : array = O(1) access / O(n) insert; list = O(n) access / O(1) splice. Exact opposites
Measured truth  : list wins insert-at-front ~20-40x; array wins indexing ~3000x+ and traversal ~9x (cache)
Language lesson : C can leak and use-after-free; Java/Python cannot; Rust makes cycles unrepresentable
Security        : CWE-416 use-after-free, CWE-415 double free, CWE-401 leak, CWE-835 infinite loop on a cycle
Takeaway        : choose a list only for O(1) splicing at a node you already hold; otherwise prefer an array or deque
```

## 12. References

- Cormen, Leiserson, Rivest, Stein: *Introduction to Algorithms*, 4th ed., ch. 10.2 (linked lists).
- Kernighan & Ritchie: *The C Programming Language*, 2nd ed., ch. 6.5 (self-referential structures).
- Knuth: *The Art of Computer Programming*, Vol. 1, §2.2.3 (linked allocation) — the original treatment, and §2.3 for Floyd's method.
- *Learn Rust With Entirely Too Many Linked Lists*: <https://rust-unofficial.github.io/too-many-lists/> — the canonical explanation of why this structure is hard in Rust.
- *The Rust Programming Language*, ch. 15 (`Box`, `Rc`, `RefCell`, and reference cycles): <https://doc.rust-lang.org/book/ch15-06-reference-cycles.html>
- Java API, `java.util.LinkedList` (doubly linked, O(1) at both ends): <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/LinkedList.html>
- Python docs, `collections.deque` and `list` time complexity: <https://wiki.python.org/moin/TimeComplexity>
- Drepper, *What Every Programmer Should Know About Memory* (2007) — the cache behaviour behind §5.
- MITRE CWE-416 (use after free), CWE-415 (double free), CWE-401 (memory leak), CWE-476 (NULL dereference), CWE-835 (infinite loop).
