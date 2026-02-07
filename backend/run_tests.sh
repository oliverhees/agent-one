#!/bin/bash
# Run all test files sequentially to avoid cross-test deadlocks.
# Each file gets its own pytest session with fresh DB setup/teardown.
set -eo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate

TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_FILES=""
ALL_PASSED=true

echo "Running tests sequentially per file..."
echo ""

for test_file in tests/test_*.py; do
    fname=$(basename "$test_file")
    printf "%-40s " "$fname"

    # Capture output, extract summary line
    output=$(python -m pytest "$test_file" -q --no-header --tb=short --no-cov 2>&1)
    exit_code=$?

    # Extract passed/failed counts from output
    summary=$(echo "$output" | tail -1)

    if [ $exit_code -eq 0 ]; then
        printf "\033[32m%s\033[0m\n" "$summary"
    else
        printf "\033[31m%s\033[0m\n" "$summary"
        FAILED_FILES="$FAILED_FILES\n  - $fname"
        ALL_PASSED=false
    fi
done

echo ""
echo "=========================================="

if $ALL_PASSED; then
    echo -e "\033[32mALL TEST FILES PASSED\033[0m"
    exit 0
else
    echo -e "\033[31mFAILED FILES:$FAILED_FILES\033[0m"
    exit 1
fi
