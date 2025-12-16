#!/bin/bash
set -e

# Strict CI check - number of type errors must exactly match scripts/type-errors.json
# This script is for CI only - use npm run typecheck:update-baseline locally

echo "Running type check..."
OUTPUT=$(npm run typecheck 2>&1 || true)
echo "$OUTPUT"

# Extract error and warning counts
CURRENT_ERRORS=$(echo "$OUTPUT" | grep -o 'found [0-9]* error' | grep -o '[0-9]*' | head -1 || echo "0")
CURRENT_WARNINGS=$(echo "$OUTPUT" | grep -o 'and [0-9]* warning' | grep -o '[0-9]*' | head -1 || echo "0")

# Read baseline
BASELINE_ERRORS=$(node -p "require('./scripts/type-errors.json').errorCount")
BASELINE_WARNINGS=$(node -p "require('./scripts/type-errors.json').warningCount")

echo ""
echo "======================================"
echo "Type Check Baseline Comparison"
echo "======================================"
echo "Errors:   $BASELINE_ERRORS (baseline) vs $CURRENT_ERRORS (current)"
echo "Warnings: $BASELINE_WARNINGS (baseline) vs $CURRENT_WARNINGS (current)"
echo ""

if [ "$CURRENT_ERRORS" -gt "$BASELINE_ERRORS" ]; then
  ADDED=$((CURRENT_ERRORS - BASELINE_ERRORS))
  echo "❌ FAILED: Type errors increased by $ADDED"
  echo ""
  echo "You introduced $ADDED new type error(s)."
  echo "Please fix them before merging."
  echo ""
  exit 1
elif [ "$CURRENT_ERRORS" -lt "$BASELINE_ERRORS" ]; then
  FIXED=$((BASELINE_ERRORS - CURRENT_ERRORS))
  echo "❌ FAILED: Type errors decreased by $FIXED but baseline not updated"
  echo ""
  echo "Great! You fixed $FIXED type error(s)! 🎉"
  echo ""
  echo "Please update the baseline by running:"
  echo "  npm run typecheck:update-baseline"
  echo ""
  echo "Then commit the updated scripts/type-errors.json file in this PR."
  echo ""
  exit 1
else
  echo "✅ PASSED: Type errors match baseline ($CURRENT_ERRORS errors)"
fi

echo "======================================"
