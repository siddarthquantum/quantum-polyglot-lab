# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Doubly linked lists in four languages, four containers, one published report.** C, Java, Python and Rust (`<lang>/doubly_linked_list/`) with push/pop at both ends, insert, delete by position and by value, search, nearer-end `get`, O(1) removal of a held node, reverse, and an integrity check modelled on glibc's safe unlinking (the demo corrupts a link and shows removal refused). All four print `shared/doubly_linked_list/expected_demo.txt` and agree on benchmark checksums; `run_all.sh` adds the ASan/UBSan leak check and 9 Rust unit tests. The Rust version is a generational arena: links are indices, and stale handles are rejected. Each language also builds into its own multi-stage image (distroless for C, Java and Rust) and runs non-root, with no network, a read-only root, all capabilities dropped and pid/memory limits (`docker/doubly_linked_list/`). New `report.yml` workflow builds the containers, verifies output, checksums and isolation via `docker inspect` (`tools/report/collect.py`), renders a static report (`tools/report/build_report.py`), attaches it to pull requests and deploys it to GitHub Pages from `main`. Guide: `shared/doubly_linked_list/README.md`.
- **Linked lists in four languages:** a full singly linked list in C, Java, Python and Rust (`c/`, `java/`, `python/`, `rust/` `linked_list/`) with traverse, insert at any position, delete by position and by value, search, indexed get, reverse, find-middle (tortoise and hare), Floyd cycle detection and clear. All four print the same `shared/linked_list/expected_demo.txt` **and** must produce identical benchmark checksums, so the speed comparison comes from provably equal work. `shared/linked_list/run_all.sh` builds with warnings as errors, verifies the C build is leak-free and UB-free under ASan/UBSan, and runs 8 Rust unit tests. The guide (`shared/linked_list/README.md`) covers the pointer model, a full complexity table, the three interview algorithms, a measured array-vs-linked-list head-to-head, a four-language memory-model comparison (including why a cycle is unrepresentable with Rust's `Box`) and the related CWEs. New CI job runs the cross-language check; CodeQL now also builds the C version.
- **Revision docs:** `docs/highlights.md` (compact complexity, trade-off and security reference) and `docs/mistakes.md` (borrow-checker aliasing on argument evaluation, the recursive `Drop` threshold measured per build mode, and why benchmarks need checksums).
- **Array basics in four languages:** traverse, insert and delete on a fixed-capacity array in C, Java, Python and Rust (`c/`, `java/`, `python/`, `rust/` `array_basics/`). All four must print the same `shared/array_basics/expected_demo.txt`; `shared/array_basics/run_all.sh` builds them with warnings as errors (C also under ASan/UBSan), runs Rust unit tests and, with `bench`, a speed comparison. The beginner guide (`shared/array_basics/README.md`) covers Big-O/Ω/Θ, a complexity table, measured speed results and a memory-safety comparison. New CI job runs the cross-language check.
- **C array lab:** exercise file with ten array operations to implement (print, insert, delete, linear and binary search, insertion sort, reverse, rotate, max/min/sum), a reference solution, and 22 shared test cases covering empty and full arrays, invalid positions, `long long` sums and malformed input. CI compiles the exercise and tests the solution under ASan/UBSan.
- GitHub Actions CI: C build with warnings as errors, tests under ASan/UBSan, Python lint, CodeQL and gitleaks secret scanning.
- Shared test runner and cases for the C graph traversal lab, including invalid-input and dense-graph cases.
- Contributing guide, security policy, code of conduct and this changelog.

### Fixed
- **C graph traversal:** DFS stack overflowed on dense graphs (a vertex can be pushed once per edge, so the stack needs V² slots, not V). Found with AddressSanitizer on a complete 100-vertex graph.
- **C graph traversal:** vertex numbers from input were used as array indexes without checks; invalid edges and start vertices are now rejected.
- **Python clustering lab:** removed a duplicate agglomerative clustering run on the full dataset that could hang; the sampled run is kept.
- **Python clustering lab:** dataset path can now be passed as an argument, with a clear message when the file is missing.

### Removed
- Compiled binary `c/graph_lab/graph` that had been committed to the repo.

### Changed
- Renamed `grapgh_traversals.c` to `graph_traversals.c`.

## 2026-09-12

### Added
- Repository scaffolding, README and learning methodology.
- Book chapter: mathematical foundations of integer and floating-point addition.
- C graph traversal lab (BFS and DFS) and Python clustering lab (K-Means, DBSCAN, agglomerative).
