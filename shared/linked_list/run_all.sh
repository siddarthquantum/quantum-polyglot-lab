#!/usr/bin/env bash
# Builds the C, Java, Python and Rust linked_list programs, checks that all four
# print exactly shared/linked_list/expected_demo.txt, then (optionally) benchmarks them.
#
# Usage (from the repo root):
#   shared/linked_list/run_all.sh          # build + verify demo output + Rust unit tests
#   shared/linked_list/run_all.sh bench    # ...and run the speed comparison
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HERE="$ROOT/shared/linked_list"
BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT

echo "== build"
gcc -std=c11 -Wall -Wextra -Werror -O2 -o "$BUILD/linked_list_c" "$ROOT/c/linked_list/linked_list.c"
gcc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -o "$BUILD/linked_list_c_asan" "$ROOT/c/linked_list/linked_list.c"
javac -Xlint:all -Werror -d "$BUILD/java" "$ROOT/java/linked_list/LinkedListLab.java"
rustc -O --edition 2021 -D warnings -o "$BUILD/linked_list_rs" "$ROOT/rust/linked_list/linked_list.rs"
rustc --edition 2021 -D warnings --test -o "$BUILD/linked_list_rs_test" "$ROOT/rust/linked_list/linked_list.rs"

declare -A RUN=(
    [C]="$BUILD/linked_list_c"
    [C-ASan]="$BUILD/linked_list_c_asan"
    [Java]="java -cp $BUILD/java LinkedListLab"
    [Python]="python3 $ROOT/python/linked_list/linked_list.py"
    [Rust]="$BUILD/linked_list_rs"
)

echo "== demo output must match expected_demo.txt"
fail=0
for lang in C C-ASan Java Python Rust; do
    if diff <(${RUN[$lang]} 2>/dev/null) "$HERE/expected_demo.txt" >/dev/null; then
        echo "PASS  $lang"
    else
        echo "FAIL  $lang"; diff <(${RUN[$lang]} 2>/dev/null) "$HERE/expected_demo.txt" || true; fail=1
    fi
done

# The ASan build also proves there is no leak: every malloc'd node is freed.
# AddressSanitizer reports leaks on exit, and a non-zero exit code fails here.
echo "== C must be leak-free and UB-free (ASan + UBSan, demo and bench)"
"$BUILD/linked_list_c_asan" >/dev/null
"$BUILD/linked_list_c_asan" bench >/dev/null
echo "PASS  C-ASan (no leaks, no undefined behaviour)"

echo "== Rust unit tests"
"$BUILD/linked_list_rs_test" -q

echo "== all four must agree on the benchmark checksums"
# Same data, same work: if any checksum differs, the implementations diverged.
ref=""
for lang in C Java Python Rust; do
    sums="$(${RUN[$lang]} bench 2>/dev/null | awk '{print $1, $2}')"
    if [[ -z "$ref" ]]; then
        ref="$sums"
    elif [[ "$sums" != "$ref" ]]; then
        echo "FAIL  $lang checksums differ"; diff <(echo "$ref") <(echo "$sums") || true; fail=1
    fi
done
[[ $fail -eq 0 ]] && echo "PASS  checksums identical across C, Java, Python, Rust"

[[ $fail -eq 0 ]] || exit 1

if [[ "${1:-}" == "bench" ]]; then
    echo "== benchmark (best of 3 rounds; build_front/pop_front = 200,000 nodes;"
    echo "   traverse = 10 passes; index_access = 200 get(i) calls on 20,000 nodes)"
    for lang in C Java Python Rust; do
        echo "-- $lang"
        ${RUN[$lang]} bench 2>/dev/null
    done
fi
