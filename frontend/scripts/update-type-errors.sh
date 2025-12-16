#!/bin/bash
set -e

# Update the scripts/type-errors.json file
# Run this locally after fixing type errors

echo "Running type check..."
OUTPUT=$(npm run typecheck 2>&1 || true)
echo "$OUTPUT"

# Extract error and warning counts (macOS/BSD compatible)
CURRENT_ERRORS=$(echo "$OUTPUT" | grep -o 'found [0-9]* error' | grep -o '[0-9]*' | head -1 || echo "0")
CURRENT_WARNINGS=$(echo "$OUTPUT" | grep -o 'and [0-9]* warning' | grep -o '[0-9]*' | head -1 || echo "0")

# Read current baseline
BASELINE_ERRORS=$(node -p "require('./scripts/type-errors.json').errorCount")
BASELINE_WARNINGS=$(node -p "require('./scripts/type-errors.json').warningCount")

echo ""
echo "======================================"
echo "Updating Type Check Baseline"
echo "======================================"
echo "Current baseline: $BASELINE_ERRORS errors, $BASELINE_WARNINGS warnings"
echo "New count:        $CURRENT_ERRORS errors, $CURRENT_WARNINGS warnings"
echo ""

if [ "$CURRENT_ERRORS" -eq "$BASELINE_ERRORS" ]; then
  echo "✅ No change in error count - baseline already up to date"
  echo "======================================"
  exit 0
fi

# Update the baseline file
node -e "
  const fs = require('fs');
  const baseline = require('./scripts/type-errors.json');
  baseline.errorCount = $CURRENT_ERRORS;
  baseline.warningCount = $CURRENT_WARNINGS;
  baseline.lastUpdated = new Date().toISOString().split('T')[0];
  fs.writeFileSync('./scripts/type-errors.json', JSON.stringify(baseline, null, 2) + '\n');
"

if [ "$CURRENT_ERRORS" -lt "$BASELINE_ERRORS" ]; then
  FIXED=$((BASELINE_ERRORS - CURRENT_ERRORS))
  echo "🎉 Baseline updated! You fixed $FIXED type error(s)!"
else
  ADDED=$((CURRENT_ERRORS - BASELINE_ERRORS))
  echo "⚠️  Baseline updated. You added $ADDED type error(s)."
fi

echo ""
echo "Next steps:"
echo "  git add scripts/type-errors.json"
echo "  git commit -m 'chore: update type-errors.json ($BASELINE_ERRORS → $CURRENT_ERRORS errors)'"
echo ""
echo "======================================"
