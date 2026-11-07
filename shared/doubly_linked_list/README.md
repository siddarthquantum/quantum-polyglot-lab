# Doubly Linked Lists in Four Languages, Four Containers

**Read `shared/linked_list/README.md` first.** The singly linked list made one trade against the array. The doubly linked list adds one pointer per node and changes three operations from O(n) to O(1). This guide is about what that pointer buys, what it costs, and why the same twenty lines are routine in Java, risky in C, and a design decision in Rust.

| Language | Source | Container |
| --- | --- | --- |
| C | [`c/doubly_linked_list/doubly_linked_list.c`](../../c/doubly_linked_list/doubly_linked_list.c) | [`c.Dockerfile`](../../docker/doubly_linked_list/c.Dockerfile) |
| Java | [`java/doubly_linked_list/DoublyLinkedListLab.java`](../../java/doubly_linked_list/DoublyLinkedListLab.java) | [`java.Dockerfile`](../../docker/doubly_linked_list/java.Dockerfile) |
| Python | [`python/doubly_linked_list/doubly_linked_list.py`](../../python/doubly_linked_list/doubly_linked_list.py) | [`python.Dockerfile`](../../docker/doubly_linked_list/python.Dockerfile) |
| Rust | [`rust/doubly_linked_list/doubly_linked_list.rs`](../../rust/doubly_linked_list/doubly_linked_list.rs) | [`rust.Dockerfile`](../../docker/doubly_linked_list/rust.Dockerfile) |

```bash
shared/doubly_linked_list/run_all.sh                     # native: parity, ASan leak check, Rust tests, checksums
shared/doubly_linked_list/run_all.sh bench               # ...plus timings
docker compose -f docker/doubly_linked_list/compose.yaml up --build    # all four, each in its own container
tools/report/local.sh                                                 # build, verify, report at http://localhost:8080
```

---

## 1. One more pointer

```text
head                                  tail
 │                                     │
 ▼                                     ▼
┌───┬────┬───┐   ┌───┬────┬───┐   ┌───┬────┬───┐
│ / │ 10 │ ●─┼──▶│   │ 20 │ ●─┼──▶│   │ 30 │ / │
│   │    │   │◀──┼─● │    │   │◀──┼─● │    │   │
└───┴────┴───┘   └───┴────┴───┘   └───┴────┴───┘
 prev value next
```

Every node knows both neighbours, and the list knows both ends. Two rules follow:

1. **Every link exists twice.** If `a.next` is `b`, then `b.prev` must be `a`. Every insert and delete has to update both directions, and the whole correctness argument for this structure is "the two directions always agree". Section 4 shows what happens when they don't.
2. **No node is ever hard to reach.** Its predecessor is one pointer away, so you never need to walk from the head to find "the node before this one".

### Inserting: four writes, in an order that never loses the list

Insert 99 before 30:

```text
before:   [10] ⇄ [20] ⇄ [30]

1. new node points at both neighbours        [20] ← [99] → [30]
2. neighbours point at the new node          [10] ⇄ [20] ⇄ [99] ⇄ [30]
```

Step 1 only writes into the new node, which nothing else can see yet, so the list stays valid until step 2. The singly linked rule ("point the new node at the rest first") becomes "wire the new node completely, then publish it".

### Removing a node you hold: two writes, no walk

```text
node.prev.next = node.next      [10] ⇄ [20] ───────▶ [30]
node.next.prev = node.prev      [10] ⇄ [20] ⇄ [30]          [99] detached
```

This is the operation that justifies the extra pointer. In a singly linked list, removing a node you hold costs O(n), because you must walk from the head to find its predecessor.

---

## 2. Complexity: what the prev pointer changes

| Operation | Array | Singly linked | **Doubly linked** | Why |
| --- | --- | --- | --- | --- |
| `get(i)` | **Θ(1)** | Θ(n) | Θ(min(i, n−i)) | walk from the nearer end: at most n/2 steps, still Θ(n) |
| push_front | Θ(n) | Θ(1) | **Θ(1)** | |
| push_back | Θ(1)* | Θ(n)† | **Θ(1)** | the tail pointer |
| pop_front | Θ(n) | Θ(1) | **Θ(1)** | |
| pop_back | Θ(1) | Θ(n) | **Θ(1)** | the new node's prev is the new tail |
| remove a **held** node | Θ(n) | Θ(n) | **Θ(1)** | the predecessor is one pointer away |
| insert before a held node | Θ(n) | Θ(n) | **Θ(1)** | same reason |
| search by value | Θ(n) | Θ(n) | Θ(n) | nothing helps an unsorted search |
| reverse | Θ(n) | Θ(n) | Θ(n) | swap prev/next on every node, swap head/tail |
| traverse backwards | Θ(n) | Θ(n) + Θ(n) space | **Θ(n), O(1) space** | follow prev |
| memory per `int` (x86-64) | 4 B | 16 B | **24 B** | 4 value + 4 padding + 8 prev + 8 next |

\* amortized. † Θ(1) if a tail pointer is kept; `c/linked_list/` deliberately doesn't.

**The two rows that matter are "remove a held node" and "memory".** The structure costs six times an array's memory for `int` data. That is only worth paying when your workload removes or splices nodes it already holds. The canonical case is an **LRU cache**: a hash map gives O(1) lookup of the node for a key, and the doubly linked list moves that node to the front, or evicts the tail, in O(1). Neither structure can do it alone, which is why it is one of the most-asked design questions in interviews.

> **"Held" is the whole trick.** `remove_node(handle)` is O(1). `delete_value(30)` is still O(n), because finding the node is a search. The prev pointer makes *unlinking* free, not *finding*.

### Walking from the nearer end

`get(i)` and `insert(i)` start from the head when `i < n − i` and from the tail otherwise. The demo prints which end it used:

```text
get at 1         : 20  (1 step from head)
get at 3         : 40  (1 step from tail)
```

This halves the worst case. It does not change the Big-O: Θ(n/2) is Θ(n).

---

## 3. What all four programs do

Same operations, same messages, byte-identical output (`expected_demo.txt`):

`push_front`, `push_back`, `pop_front`, `pop_back`, `insert(pos)`, `delete_at(pos)`, `delete_value`, `search`, `find` (returns a handle), `remove_node(handle)`, `get(pos)` from the nearer end, forward and backward traversal, `reverse`, `check` (integrity), `clear`.

`run_all.sh` fails the build unless all four print the expected demo, the C build is clean under AddressSanitizer + UndefinedBehaviorSanitizer (leaks included), the 9 Rust unit tests pass, and **all four benchmark checksums match**. Checksums matter because four programs can each "finish" while doing different amounts of work, and then the timing comparison means nothing.

---

## 4. Safe unlinking: the security lesson in this file

Look at `remove_node` in any of the four files. Before it changes anything, it checks that both neighbours agree they point at this node:

```c
if (node->prev != NULL ? node->prev->next != node : l->head != node) return ERR_CORRUPT;
if (node->next != NULL ? node->next->prev != node : l->tail != node) return ERR_CORRUPT;
```

That check is copied from **glibc's `malloc`**. glibc keeps its free memory chunks on doubly linked lists. Before around 2004, freeing a chunk ran the unlink without checking:

```c
FD = P->fd;  BK = P->bk;
FD->bk = BK;  BK->fd = FD;   /* two writes through pointers stored IN the chunk */
```

A heap overflow lets an attacker overwrite `fd` and `bk` in the next chunk. The unlink then performs `*(fd + offset) = bk`: **a write of an attacker-chosen value to an attacker-chosen address**. Point it at a function pointer or a return address and that is code execution. This is the classic "unlink" exploit. glibc's fix is the check above, and it still aborts with the message our programs print:

```text
corrupt node 20  : prev now points at itself
integrity check  : error: corrupted double-linked list at index 1
remove node 20   : error: corrupted double-linked list
```

Three things to take from it:

- **A data structure invariant is a security property.** "Both directions agree" sounds like tidiness. In an allocator, it is what stands between a one-byte overflow and remote code execution.
- **Validate before you write, not after.** The check costs two comparisons. Running it after the writes would be useless, because the damage is already done.
- **The checker must not trust the structure it checks.** `check()` caps its walk at `len + 1` steps, so a corrupted list containing a cycle can't make the integrity check loop forever (CWE-835).

| CWE | In a doubly linked list |
| --- | --- |
| CWE-416 use after free | using a handle after `remove_node` freed it (C); a stale arena index (Rust, see §5) |
| CWE-415 double free | removing the same handle twice |
| CWE-787 out-of-bounds write | the unlink write primitive above |
| CWE-401 memory leak | forgetting `free` (C), or a reference cycle nobody breaks |
| CWE-835 infinite loop | traversing a corrupted list with a cycle |

---

## 5. Four memory models, one structure

The singly linked list was hardest in C, because you manage every byte. The doubly linked list is hardest in **Rust**, and the reason teaches more than the code.

### C: you own every pointer

Two pointers per node, both maintained by hand, `free` on removal. Every mistake from §4 is possible. ASan in `run_all.sh` catches the memory ones, and nothing catches a prev pointer that disagrees with a next pointer except `check()`.

### Java: the GC owns the memory, not the invariant

No `free`, so no use-after-free or double free. The program can still build the corrupted list from §4 (the demo does it), and `removeNode` still has to refuse it. **Garbage collection makes memory errors impossible. It does not make logic errors impossible.**

### Python: a structure made entirely of reference cycles

`a.next is b` and `b.prev is a` form a reference cycle, so reference counting alone can never free a doubly linked list. CPython's cycle collector eventually finds it. `clear()` breaks every link by hand so the memory comes back immediately. Real code uses `collections.deque`, a C-implemented doubly linked list of blocks.

### Rust: when a node has two parents, ownership has to change

`rust/linked_list/` used `Option<Box<Node>>`, where each node owns the next. A doubly linked node is pointed at by two neighbours, and `Box` means **one** owner. That doesn't compile, and there are three ways out:

| Approach | Safe? | Cost | Used by |
| --- | --- | --- | --- |
| `Rc<RefCell<Node>>` forward, `Weak` back | yes | refcount updates and a runtime borrow check on every access; awkward code | teaching material |
| raw pointers in `unsafe` | no, C's rules | none | `std::collections::LinkedList` |
| **arena: nodes in a `Vec`, links are indices** | **yes** | an index lookup per step | this file; LRU and graph crates |

An index can't dangle into freed memory. But freed slots are reused, so an old index can name a **different, live** node. That is the arena's version of use-after-free: memory-safe, still a bug. The fix is a **generational index**. Each slot counts how many times it has been freed, a `Handle` remembers the count it was issued with, and a mismatch returns `StaleHandle`:

```rust
let old = l.find(2).unwrap();
l.remove_node(old).unwrap();
let fresh = l.push_back(99);                       // reuses the freed slot
assert_eq!(fresh.index, old.index);                // same index...
assert_eq!(l.remove_node(old), Err(ListError::StaleHandle));  // ...but the old handle is rejected
```

That test is in the file, alongside one proving that `clear()` invalidates every handle. (Truncating the `Vec` would reset generations to 0 and let an old handle match a new node. That is a bug I designed around, not one I hit.)

**Measured cost of the safe version.** `std::mem::size_of` on this layout:

| Node | Size | Why |
| --- | --- | --- |
| C `{int, Node*, Node*}` | 24 B | 4 + 4 padding + 8 + 8 |
| Rust arena slot, `Option<usize>` links | **48 B** | each `Option<usize>` is 16 B, plus generation and live flag |
| Rust slot with `u32` indices, `u32::MAX` as nil | 16 B | not used here; left as an exercise |

The slot is twice the size of a C node, and that shows up in the traversal numbers below.

---

## 6. Measured: native, same machine

`run_all.sh bench`, best of 3 rounds, two separate runs. 2-core Intel Xeon @ 2.10 GHz, gcc 13.3 `-O2`, OpenJDK 21.0.12, CPython 3.13.18, rustc 1.97 `-O`. **All four print identical checksums.** CI publishes container numbers from its own runner; compare ratios across machines, never absolute times.

| Workload | C | Rust | Java | Python |
| --- | --- | --- | --- | --- |
| build_back (200k push_back) | **1.53–1.87 ms** | 1.61–1.67 ms | 4.11–4.28 ms | 34.7–35.3 ms |
| traverse (10 passes, alternating) | **4.17–4.85 ms** | 8.19–8.63 ms | 4.44–4.61 ms | 55.1–56.8 ms |
| remove_held (100k by handle) | 0.57–1.08 ms | 0.94–0.96 ms | **0.36–0.49 ms** | 17.0 ms |
| pop_back (100k) | 0.64–0.82 ms | 0.88–0.90 ms | **0.43–0.65 ms** | 21.8–22.0 ms |
| index_access (200 gets on 20k) | 4.13–5.21 ms | **2.91–2.93 ms** | 2.87–2.93 ms | 14.8 ms |

What the numbers say:

1. **`remove_held` is the point of the structure.** 100,000 removals in about half a millisecond. A singly linked list must find each predecessor first, which makes the same job quadratic.
2. **Rust's traversal is about 2× C's**, and §5 explains it: each step reads a 48-byte slot instead of a 24-byte node, plus a bounds-checked `Vec` index. The safe design has a measurable cost, and the 16-byte layout is how you would buy it back.
3. **Java wins the removal-heavy workloads**, as it did in the singly linked list. Unlinking is a few pointer writes, and the JIT-compiled loop is as tight as C's.
4. **Python is about 20× slower** than the fastest language on build_back, and 10–13× on the others. Each node is a full object, and every attribute access goes through the interpreter.
5. **An open question worth investigating:** on `index_access`, C (4.1–5.2 ms) is slower than Rust and Java (about 2.9 ms), although all three do the same walk. A plausible cause is node placement: the Rust arena and Java's bump allocator put consecutive nodes next to each other, while `malloc` gives no such guarantee. That is a hypothesis, not a measurement. Testing it (for example, by allocating C nodes from one block) is a good exercise.

---

## 7. Four isolated containers

Each language builds into its own image and runs in its own container. The four never share a filesystem, a network or a process namespace.

| | C | Java | Python | Rust |
| --- | --- | --- | --- | --- |
| Build stage | `gcc:14` | `eclipse-temurin:21-jdk` | (none) | `rust:1-slim-bookworm` |
| Runtime image | `distroless/static` | `distroless/java21` | `python:3.12-slim` | `distroless/cc` |
| What ships | one static binary | JRE + `.class` file | interpreter + `.py` | binary + glibc |
| Shell in the image? | no | no | yes | no |

**Multi-stage builds** keep compilers out of the runtime image. The C image ships the binary and nothing else, with no shell, no package manager and no libc to patch. Python has to ship an interpreter, so its image is the largest and the only one with a shell. The published report shows the real image sizes from CI.

### The hardening, and why each line is there

All four services inherit one block in [`compose.yaml`](../../docker/doubly_linked_list/compose.yaml):

| Setting | What it removes | OS-security concept |
| --- | --- | --- |
| `user: 65532:65532` | root inside the container | least privilege |
| `network_mode: none` | every interface but loopback | no channel to leak data or fetch a payload |
| `read_only: true` | writes to the root filesystem | an attacker can't drop or modify a binary |
| `tmpfs /tmp noexec,nosuid` | executing anything written to the one writable path | W^X at the filesystem level |
| `cap_drop: [ALL]` | every Linux capability (`CAP_NET_RAW`, `CAP_CHOWN`, …) | root's power split into revocable pieces, all revoked |
| `no-new-privileges` | gaining privilege through setuid binaries | the privilege set can only shrink |
| `pids_limit: 64` | fork bombs (the JVM needs about 25 threads) | resource isolation (cgroups) |
| `mem_limit`, `cpus` | starving the host | resource isolation (cgroups) |

If you are studying protection in operating systems: Linux capabilities split the all-or-nothing superuser into fine-grained privileges, and `cap_drop: ALL` is the principle of least privilege applied to that list. Namespaces and cgroups are the kernel mechanisms underneath; the container is just a convenient way to ask for them.

**The report doesn't trust this file.** `tools/report/collect.py` reads every setting back with `docker inspect` from the container that actually ran, and **fails the build** if any container runs as root, has a network, has a writable root, keeps a capability, or lacks a limit.

---

## 8. The report, on localhost

```text
tools/report/local.sh
   │
   ├─ collect.py ─▶ build 4 images ─▶ run demo + bench in each ─▶ docker inspect ─▶ fail on any gap
   ├─ build_report.py ─▶ site/index.html + site/results.json
   └─ compose --profile report up ─▶ nginx-unprivileged ─▶ http://localhost:8080
```

```bash
tools/report/local.sh          # build, verify, render, serve
tools/report/local.sh stop     # stop the viewer
REPORT_PORT=9000 tools/report/local.sh
```

The viewer is a fifth container with the same hardening as the other four: non-root (uid 101), read-only root, `noexec` tmpfs, no capabilities, limits. The report is mounted read-only. The port is bound to `127.0.0.1`, so the page is reachable from your machine only, not from other devices on your network. That is the difference between `-p 8080:8080` and `-p 127.0.0.1:8080:8080`, and a good thing to be able to explain.

Every number on the page comes from the run named at its top, and `results.json` is served beside it so the page can be checked against the raw data. The page is static HTML with no scripts and no external requests. CI runs the same steps on every push, starts the viewer, fetches the page over localhost, and attaches it to the run. **Nothing is published.**

---

## 9. Common mistakes

- [ ] Updating `next` but not `prev` (or the reverse). The list still prints correctly forwards and is broken backwards. `check()` exists for this.
- [ ] Forgetting the ends: removing the head must update `l->head`, removing the tail must update `l->tail`, and removing the last node must update both.
- [ ] Publishing a new node before wiring it: point the neighbours at it only after its own `prev` and `next` are set.
- [ ] Assuming `delete_value` is O(1) because unlinking is. Finding the node is still a search.
- [ ] C: reading `node->value` after `free(node)`.
- [ ] Python: relying on refcounting to free a list of cycles.
- [ ] Rust: reusing an index without a generation check. That is a logic-level use-after-free.
- [ ] Trusting a list from elsewhere without `check()`, then looping forever on a cycle.

## 10. Revision questions

1. Which three operations does the prev pointer make O(1), and why does each need it?
2. `remove_node(handle)` is O(1) but `delete_value(v)` is O(n). Explain the difference in one sentence.
3. Insert X between A and B: write the four assignments in a safe order, and say what an observer could see if you did them in the wrong order.
4. How does an LRU cache combine a hash map and a doubly linked list to make both `get` and eviction O(1)?
5. Explain the glibc unlink exploit: what the attacker overwrites, and what write primitive results. Which two comparisons stop it?
6. Why can't a doubly linked list be built from `Box` in safe Rust? Name the three alternatives and one cost of each.
7. What is a stale index in an arena, and how does a generational index detect it?
8. Why is a Rust arena slot with `Option<usize>` links 48 bytes? How would you get it to 16?
9. Name four settings in `compose.yaml`, what each removes, and why `cap_drop: ALL` is least privilege.
10. Why does the C image need no shell, and why must the Python image ship one?

## 11. Quick review

```text
Structure      : each node has prev + next; the list keeps head + tail
Invariant      : a.next == b  ⇔  b.prev == a, at every link. Correctness AND security
O(1)           : push/pop at both ends, remove or insert at a HELD node
Still O(n)     : search, get(i) (but from the nearer end: ≤ n/2 steps)
Memory         : 24 B per int node in C (6× an array); 48 B per Rust arena slot
Security       : glibc safe unlinking, i.e. check both neighbours before writing; unlink exploit = CWE-787
Rust           : two parents means no Box. Use an arena with generational indices
Containers     : 4 images, distroless where possible; non-root, no network, read-only, no caps, limits
Evidence       : identical output + identical checksums + docker inspect, on every push
```

## 12. References

- Cormen et al., *Introduction to Algorithms*, 4th ed., §10.2 (doubly linked lists with sentinels).
- glibc `malloc/malloc.c`, `unlink_chunk` and the "corrupted double-linked list" check.
- Phrack 57:8, "Vudo malloc tricks", and 57:9, "Once upon a free()": the original unlink exploitation write-ups.
- *Learn Rust With Entirely Too Many Linked Lists*, chapters on the doubly linked deque: <https://rust-unofficial.github.io/too-many-lists/>
- *The Rust Programming Language*, ch. 15.6, reference cycles and `Weak`: <https://doc.rust-lang.org/book/ch15-06-reference-cycles.html>
- Python docs, garbage collector and reference cycles: <https://docs.python.org/3/library/gc.html>
- Docker docs, *Security* and `docker run` runtime privileges and Linux capabilities: <https://docs.docker.com/engine/security/>
- `capabilities(7)` and `prctl(2)` (`PR_SET_NO_NEW_PRIVS`) man pages.
- Google distroless images: <https://github.com/GoogleContainerTools/distroless>
- MITRE CWE-416, CWE-415, CWE-787, CWE-401, CWE-835.
