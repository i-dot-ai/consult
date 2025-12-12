#!/bin/bash
set -e

# Run typecheck and capture output
echo "Running type check..."
OUTPUT=$(npm run typecheck 2>&1 || true)
echo "$OUTPUT"

# Extract error and warning counts
CURRENT_ERRORS=$(echo "$OUTPUT" | grep -oP 'found \K\d+(?= errors)' || echo "0")
CURRENT_WARNINGS=$(echo "$OUTPUT" | grep -oP 'and \K\d+(?= warnings)' || echo "0")

# Read baseline
BASELINE_ERRORS=$(node -p "require('./.typecheck-baseline.json').errorCount")
BASELINE_WARNINGS=$(node -p "require('./.typecheck-baseline.json').warningCount")

echo ""
echo "======================================"
echo "Type Check Baseline Comparison"
echo "======================================"
echo "Errors:   $BASELINE_ERRORS → $CURRENT_ERRORS"
echo "Warnings: $BASELINE_WARNINGS → $CURRENT_WARNINGS"
echo ""

# Check if we're on main branch (for updating baseline)
IS_MAIN=${IS_MAIN:-false}

if [ "$CURRENT_ERRORS" -gt "$BASELINE_ERRORS" ]; then
  echo "❌ FAILED: Type errors increased from $BASELINE_ERRORS to $CURRENT_ERRORS"
  echo ""
  echo "Please fix the new type errors before merging."
  echo "If you need help, run: npm run typecheck"
  exit 1
elif [ "$CURRENT_ERRORS" -lt "$BASELINE_ERRORS" ]; then
  FIXED=$((BASELINE_ERRORS - CURRENT_ERRORS))
  echo "✅ SUCCESS: Type errors decreased! Fixed $FIXED error(s)! 🎉"

  if [ "$IS_MAIN" = "true" ]; then
    echo ""
    echo "Updating baseline file..."
    node -e "
      const fs = require('fs');
      const baseline = require('./.typecheck-baseline.json');
      baseline.errorCount = $CURRENT_ERRORS;
      baseline.warningCount = $CURRENT_WARNINGS;
      baseline.lastUpdated = new Date().toISOString().split('T')[0];
      fs.writeFileSync('./.typecheck-baseline.json', JSON.stringify(baseline, null, 2) + '\n');
    "
    echo "Baseline updated to $CURRENT_ERRORS errors, $CURRENT_WARNINGS warnings"
  fi
else
  echo "✅ PASSED: No change in type errors (maintaining $CURRENT_ERRORS errors)"
fi

echo "======================================"
