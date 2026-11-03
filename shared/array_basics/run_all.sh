#!/usr/bin/env bash
# Builds the C, Java, Python and Rust array_basics programs, checks that all four
# print exactly shared/array_basics/expected_demo.txt, then (optionally) benchmarks them.
#
# Usage (from the repo root):
#   shared/array_basics/run_all.sh          # build + verify demo output + Rust unit tests
#   shared/array_basics/run_all.sh bench    # ...and run the speed comparison
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HERE="$ROOT/shared/array_basics"
BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT

echo "== build"
gcc -std=c11 -Wall -Wextra -Werror -O2 -o "$BUILD/array_basics_c" "$ROOT/c/array_basics/array_basics.c"
gcc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -o "$BUILD/array_basics_c_asan" "$ROOT/c/array_basics/array_basics.c"
javac -Xlint:all -Werror -d "$BUILD/java" "$ROOT/java/array_basics/ArrayBasics.java"
rustc -O --edition 2021 -D warnings -o "$BUILD/array_basics_rs" "$ROOT/rust/array_basics/array_basics.rs"
rustc --edition 2021 -D warnings --test -o "$BUILD/array_basics_rs_test" "$ROOT/rust/array_basics/array_basics.rs"

declare -A RUN=(
    [C]="$BUILD/array_basics_c"
    [C-ASan]="$BUILD/array_basics_c_asan"
    [Java]="java -cp $BUILD/java ArrayBasics"
    [Python]="python3 $ROOT/python/array_basics/array_basics.py"
    [Rust]="$BUILD/array_basics_rs"
)

echo "== demo output must match expected_demo.txt"
fail=0
for lang in C C-ASan Java Python Rust; do
    if diff <(${RUN[$lang]} 2>/dev/null) "$HERE/expected_demo.txt" >/dev/null; then
        echo "PASS  $lang"
    else
        echo "FAIL  $lang"; diff <(${RUN[$lang]}) "$HERE/expected_demo.txt" || true; fail=1
    fi
done

echo "== Rust unit tests"
"$BUILD/array_basics_rs_test" -q

[[ $fail -eq 0 ]] || exit 1

if [[ "${1:-}" == "bench" ]]; then
    echo "== benchmark (best of 3 rounds; traverse = 10 passes over 1,000,000 ints;"
    echo "   insert/delete = 5,000 operations at index 0, the worst case)"
    for lang in C Java Python Rust; do
        echo "-- $lang"
        ${RUN[$lang]} bench
    done
fi
