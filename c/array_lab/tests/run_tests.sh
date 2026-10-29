#!/usr/bin/env bash
# Runs every case in tests/cases against a compiled binary.
#   NAME.in + NAME.expected  -> program must exit 0 and print exactly NAME.expected
#   NAME.in + NAME.fail     -> program must reject the input (non-zero exit)
# Usage: tests/run_tests.sh path/to/binary
set -u

BIN="${1:?usage: run_tests.sh path/to/binary}"
CASES="$(cd "$(dirname "$0")/cases" && pwd)"
pass=0
fail=0

for input in "$CASES"/*.in; do
    name="$(basename "$input" .in)"
    actual="$("$BIN" < "$input" 2>/dev/null)"
    status=$?

    if [[ -f "$CASES/$name.expected" ]]; then
        if [[ $status -eq 0 && "$actual" == "$(cat "$CASES/$name.expected")" ]]; then
            echo "PASS  $name"; pass=$((pass + 1))
        else
            echo "FAIL  $name (exit $status)"; fail=$((fail + 1))
            diff <(echo "$actual") "$CASES/$name.expected" | head -5
        fi
    elif [[ -f "$CASES/$name.fail" ]]; then
        if [[ $status -ne 0 ]]; then
            echo "PASS  $name (rejected as expected)"; pass=$((pass + 1))
        else
            echo "FAIL  $name (invalid input was accepted)"; fail=$((fail + 1))
        fi
    fi
done

echo "--- $pass passed, $fail failed"
[[ $fail -eq 0 ]]
