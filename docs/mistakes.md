# Learning From Mistakes

Honest record of errors, debugging discoveries and language surprises.
Format per entry: what happened, why, the fix, and the lesson.

---

## 2026-11-05 — Rust: `&mut l` and `l.len()` in the same call will not compile

**Problem:** linked list demo, Rust implementation.

**What happened**

```rust
show_insert(&mut l, "push_back 40", l.len() as i64, 40);
```

```text
error[E0502]: cannot borrow `l` as immutable because it is also borrowed as mutable
```

**Why it happened**

Arguments are evaluated while the mutable borrow for the first argument is
already live. Rust allows **either** one mutable borrow **or** any number of
shared borrows, never both at once. C and Java compile the same line happily,
which is exactly why the rule feels surprising the first time.

**How it was fixed**

Bind the value before the call, so the shared borrow ends before the mutable
borrow begins:

```rust
let end = l.len() as i64;
show_insert(&mut l, "push_back 40", end, 40);
```

**Lesson**

This is not the borrow checker being difficult — it is the same aliasing rule
that makes data races impossible. When it complains about argument evaluation,
pull the read out into a `let` above the call. Expect this every time a method
takes `&mut self` and an argument derived from `self`.

---

## 2026-11-05 — Rust: the default `Drop` on a `Box` chain is recursive

**Problem:** linked list, Rust implementation.

**What happened**

I wrote in a comment that dropping a long `Option<Box<Node>>` chain "overflows
the stack on a list of a few hundred thousand nodes", then tested it before
publishing. At 200,000 nodes in a **release** build it did **not** overflow.
The claim as written was wrong.

**Why it happened**

Each node's drop glue drops the next node, one stack frame per node — so the
recursion is real, but the frame size depends on the build. Measured:

| Nodes | Debug build | Release build |
| --- | --- | --- |
| 200,000 | **stack overflow** | fine |
| 1,000,000 | **stack overflow** | **stack overflow** |

Optimisation shrinks the frames; it does not remove the recursion.

**How it was fixed**

Implemented `Drop` for the list by calling an iterative `clear()` that pops
nodes in a loop, keeping the drop depth at one. The comment now states the
measured thresholds and names the build mode.

**Lesson**

Two lessons, and the second is the bigger one.

1. A safe abstraction is not automatically a *carefree* one. This is why
   `std::collections::LinkedList` uses raw pointers internally instead of a
   `Box` chain.
2. **Measure before you teach.** I nearly committed a plausible-sounding
   number I had not verified. "A few hundred thousand" was hand-waving; the
   real answer depends on the build mode, which is the interesting part. If a
   claim has a number in it, run the experiment.

---

## 2026-11-05 — Benchmarks that finish are not benchmarks that agree

**Problem:** cross-language comparison, all four linked list implementations.

**What happened**

Four implementations can each run a "benchmark" successfully and still be doing
different amounts of work — an off-by-one in a loop bound, or a `get` that
silently returns early, would make one language look fast for the wrong reason.

**How it was fixed**

Every benchmark prints a **checksum** alongside the time, and
`shared/linked_list/run_all.sh` fails the build unless all four checksums match
exactly. A timing comparison is only meaningful once the work is proven equal.

**Lesson**

For any performance comparison, make each implementation produce a value that
depends on all the work it did, and assert the values are identical. An
unverified benchmark measures nothing.

---

## 2026-11-07 — I expected the Rust arena to traverse faster than C. It was 2× slower.

**Problem:** doubly linked list, Rust implementation, traversal benchmark.

**What happened**

The arena keeps every node in one `Vec`, so I expected traversal to be at
least as fast as C's `malloc`'d nodes. The measurement said otherwise:

| | C | Rust arena |
| --- | --- | --- |
| traverse, 10 passes over 200k nodes | 4.2–4.8 ms | 8.2–8.6 ms |

**Why it happened**

`std::mem::size_of` gave the answer:

```text
C Node {int, Node*, Node*}                       24 bytes
Rust Slot {i32, Option<usize> ×2, u32, bool}     48 bytes   (Option<usize> alone is 16)
Rust Slot with u32 indices, u32::MAX as nil      16 bytes
```

Each step reads twice as much memory as C, through a bounds-checked index.
Contiguous storage does not help if each element is twice the size.

**How it was handled**

The 48-byte layout stays, because `Option<usize>` makes the "no neighbour"
case impossible to forget, which matters more in a teaching file. The
16-byte layout is written up in the guide as the way to buy the speed back.

**Lesson**

"Contiguous, so cache-friendly" is a hypothesis, not a result. Measure, then
look at the layout. `size_of` is a one-line experiment that explains a 2× gap.

