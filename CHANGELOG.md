# Changelog

All notable changes to this project are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
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
