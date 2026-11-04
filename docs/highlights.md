# Key Highlights

Compact revision reference. One line per idea, newest topic last.

## Complexity results

```text
Array access a[i]              → O(1)      address arithmetic
Array insert/delete at pos     → O(n)      everything after pos must shift
Array insert/delete at end     → O(1)
Dynamic array append           → O(1)      amortized (grow 1.5–2× and copy)
Linked list get(i)             → O(n)      must walk i pointers; no arithmetic
Linked list insert/delete head → O(1)      two pointer writes, nothing shifts
Linked list push_back (no tail)→ O(n)      O(1) if a tail pointer is kept
Linked list reverse            → O(n) time, O(1) space   (prev/cur/next flip)
Linked list middle             → O(n) time, O(1) space   (tortoise and hare)
Floyd cycle detection          → O(n) time, O(1) space   (beats a visited set)
BFS / DFS                      → O(V + E)
Binary search                  → O(log n)
```

## The array ↔ linked list trade-off

```text
                  array          linked list
access  a[i]      O(1)   ←win    O(n)
insert at front   O(n)           O(1)   win→
splice held node  O(n)           O(1)   win→
memory per int    4 bytes ←win   16 bytes (int + padding + pointer)
cache behaviour   sequential ←win  pointer chasing
```

Measured in C (`-O2`, n = 50,000): list beats array ~20–40× on insert-at-front;
array beats list ~3,000×+ on indexed access and ~9× on traversal.

**Rule:** equal Big-O does not mean equal speed. Traversal is Θ(n) for both, yet
the array is ~9× faster because it reads consecutive cache lines. Big-O counts
operations, not cache misses.

**Choose a linked list only** when you need O(1) splicing at a node you are
already holding (LRU cache, allocator free list, graph adjacency list).
For fast push/pop at both ends use a deque — array-backed, keeps locality.

## Language and memory model

```text
NULL            → C: NULL | Java: null | Python: None | Rust: Option::None (no null exists)
Freeing         → C: manual free() | Java/Python: GC | Rust: owner goes out of scope
Use-after-free  → C: undefined behaviour | Java/Python: impossible | Rust: compile error
Cycles          → buildable in C, Java, Python; UNREPRESENTABLE with Rust's Box
Rust cycle cost → requires Rc<RefCell<..>>, and then leaks instead of crashing (fix: Weak)
Rust footgun    → default Drop on a Box chain is RECURSIVE; overflows at 200k nodes (debug),
                  1M (release). Implement Drop with an iterative clear().
```

**Interview line:** C requires you to be correct, Rust requires you to prove it,
Java and Python make memory errors impossible but let logic errors through.
No language saves you from a wrong algorithm.

## Security

```text
CWE-416  use after free        ← stale pointer to a freed node
CWE-415  double free           ← corrupts the allocator's own free lists
CWE-401  memory leak           ← unbounded list on untrusted input = DoS
CWE-476  NULL dereference      ← missing empty / end-of-list check
CWE-835  infinite loop         ← a cycle turns every traversal into a hang
CWE-787  out-of-bounds write   ← the classic unchecked array index
CWE-125  out-of-bounds read
```
