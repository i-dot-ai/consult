#!/usr/bin/env bash
# LocalStack initialisation script — runs automatically when LocalStack reaches ready state.
#
# Sets up Lambda functions and EventBridge rules that mirror the deployed AWS architecture,
# allowing the import_candidate_themes and import_response_annotations pipeline steps to run
# locally without a deployed environment.
#
# Services used: lambda, events, iam, logs (all available on the Hobby/free tier).
# AWS Batch emulation is NOT included here — add it once an Ultimate licence is in place.

set -euo pipefail

REGION="eu-west-2"
ACCOUNT_ID="000000000000"
LAMBDA_RUNTIME="python3.12"
BUILD_DIR="/tmp/localstack-lambda-build"

# Job names must match the values in .env / docker-compose so EventBridge patterns align.
FIND_THEMES_JOB_NAME="${FIND_THEMES_BATCH_JOB_NAME:-consult-find-themes-job}"
ASSIGN_THEMES_JOB_NAME="${ASSIGN_THEMES_BATCH_JOB_NAME:-consult-assign-themes-job}"

echo "=== LocalStack init: Lambda + EventBridge setup ==="
echo "Region: $REGION"
echo "Find themes job name: $FIND_THEMES_JOB_NAME"
echo "Assign themes job name: $ASSIGN_THEMES_JOB_NAME"

# ---------------------------------------------------------------------------
# 1. IAM execution role (LocalStack doesn't validate policies — just needs an ARN)
# ---------------------------------------------------------------------------
echo ""
echo "--- Creating Lambda IAM execution role ---"
awslocal iam create-role \
  --role-name localstack-lambda-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --region "$REGION" || echo "(role already exists, continuing)"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/localstack-lambda-execution-role"

# ---------------------------------------------------------------------------
# Helper: build a Lambda deployment zip from a source directory.
#   Usage: build_lambda_zip <source_dir> <out_zip>
#   Installs requirements.txt into a package/ subdir, then zips main.py + package/.
# ---------------------------------------------------------------------------
build_lambda_zip() {
  local source_dir="$1"
  local out_zip="$2"
  local work_dir
  work_dir="$(mktemp -d)"

  echo "  Building Lambda zip from $source_dir -> $out_zip"

  # Install dependencies into work_dir/
  if [ -f "$source_dir/requirements.txt" ]; then
    pip install -q -r "$source_dir/requirements.txt" --target "$work_dir" --no-cache-dir
  fi

  # Copy handler
  cp "$source_dir/main.py" "$work_dir/main.py"

  # Zip everything
  (cd "$work_dir" && zip -r -q "$out_zip" .)

  rm -rf "$work_dir"
  echo "  Built: $out_zip ($(du -sh "$out_zip" | cut -f1))"
}

mkdir -p "$BUILD_DIR"

# ---------------------------------------------------------------------------
# 2. import_candidate_themes Lambda
# ---------------------------------------------------------------------------
echo ""
echo "--- Building import_candidate_themes Lambda package ---"

ICT_ZIP="$BUILD_DIR/import_candidate_themes.zip"
ICT_SOURCE="/etc/localstack/init/lambda/import_candidate_themes"
build_lambda_zip "$ICT_SOURCE" "$ICT_ZIP"

echo "--- Creating import_candidate_themes Lambda function ---"
awslocal lambda create-function \
  --function-name import-candidate-themes \
  --runtime "$LAMBDA_RUNTIME" \
  --handler main.lambda_handler \
  --role "$ROLE_ARN" \
  --zip-file "fileb://$ICT_ZIP" \
  --environment "Variables={REDIS_HOST=redis,REDIS_PORT=6379,ENVIRONMENT=local}" \
  --timeout 300 \
  --memory-size 512 \
  --region "$REGION" || echo "(function already exists, updating code)"

# If the function already exists from a previous run, update its code
awslocal lambda update-function-code \
  --function-name import-candidate-themes \
  --zip-file "fileb://$ICT_ZIP" \
  --region "$REGION" 2>/dev/null || true

echo "  Waiting for import-candidate-themes to become Active..."
awslocal lambda wait function-active \
  --function-name import-candidate-themes \
  --region "$REGION"

# ---------------------------------------------------------------------------
# 3. import_response_annotations Lambda
# ---------------------------------------------------------------------------
echo ""
echo "--- Building import_response_annotations Lambda package ---"

IRA_ZIP="$BUILD_DIR/import_response_annotations.zip"
IRA_SOURCE="/etc/localstack/init/lambda/import_response_annotations"
build_lambda_zip "$IRA_SOURCE" "$IRA_ZIP"

echo "--- Creating import_response_annotations Lambda function ---"
awslocal lambda create-function \
  --function-name import-response-annotations \
  --runtime "$LAMBDA_RUNTIME" \
  --handler main.lambda_handler \
  --role "$ROLE_ARN" \
  --zip-file "fileb://$IRA_ZIP" \
  --environment "Variables={REDIS_HOST=redis,REDIS_PORT=6379,ENVIRONMENT=local}" \
  --timeout 300 \
  --memory-size 512 \
  --region "$REGION" || echo "(function already exists, updating code)"

awslocal lambda update-function-code \
  --function-name import-response-annotations \
  --zip-file "fileb://$IRA_ZIP" \
  --region "$REGION" 2>/dev/null || true

echo "  Waiting for import-response-annotations to become Active..."
awslocal lambda wait function-active \
  --function-name import-response-annotations \
  --region "$REGION"

# ---------------------------------------------------------------------------
# 4. EventBridge rule: find-themes job SUCCEEDED -> import_candidate_themes
# ---------------------------------------------------------------------------
echo ""
echo "--- Creating EventBridge rule: find-themes SUCCEEDED ---"

FIND_THEMES_RULE_ARN=$(awslocal events put-rule \
  --name "import-candidate-themes-on-batch-success" \
  --event-pattern "{
    \"source\": [\"aws.batch\"],
    \"detail-type\": [\"Batch Job State Change\"],
    \"detail\": {
      \"status\": [\"SUCCEEDED\"],
      \"jobName\": [\"$FIND_THEMES_JOB_NAME\"]
    }
  }" \
  --state ENABLED \
  --region "$REGION" \
  --query RuleArn \
  --output text)

echo "  Rule ARN: $FIND_THEMES_RULE_ARN"

ICT_LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:import-candidate-themes"

awslocal lambda add-permission \
  --function-name import-candidate-themes \
  --statement-id allow-eventbridge-find-themes \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "$FIND_THEMES_RULE_ARN" \
  --region "$REGION" 2>/dev/null || echo "  (permission already exists)"

awslocal events put-targets \
  --rule "import-candidate-themes-on-batch-success" \
  --targets "[{\"Id\": \"import-candidate-themes-target\", \"Arn\": \"$ICT_LAMBDA_ARN\"}]" \
  --region "$REGION"

# ---------------------------------------------------------------------------
# 5. EventBridge rule: assign-themes job SUCCEEDED -> import_response_annotations
# ---------------------------------------------------------------------------
echo ""
echo "--- Creating EventBridge rule: assign-themes SUCCEEDED ---"

ASSIGN_THEMES_RULE_ARN=$(awslocal events put-rule \
  --name "import-response-annotations-on-batch-success" \
  --event-pattern "{
    \"source\": [\"aws.batch\"],
    \"detail-type\": [\"Batch Job State Change\"],
    \"detail\": {
      \"status\": [\"SUCCEEDED\"],
      \"jobName\": [\"$ASSIGN_THEMES_JOB_NAME\"]
    }
  }" \
  --state ENABLED \
  --region "$REGION" \
  --query RuleArn \
  --output text)

echo "  Rule ARN: $ASSIGN_THEMES_RULE_ARN"

IRA_LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:import-response-annotations"

awslocal lambda add-permission \
  --function-name import-response-annotations \
  --statement-id allow-eventbridge-assign-themes \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "$ASSIGN_THEMES_RULE_ARN" \
  --region "$REGION" 2>/dev/null || echo "  (permission already exists)"

awslocal events put-targets \
  --rule "import-response-annotations-on-batch-success" \
  --targets "[{\"Id\": \"import-response-annotations-target\", \"Arn\": \"$IRA_LAMBDA_ARN\"}]" \
  --region "$REGION"

# ---------------------------------------------------------------------------
echo ""
echo "=== LocalStack init complete ==="
echo ""
echo "Lambda functions registered:"
echo "  import-candidate-themes      (triggered by: find-themes job SUCCEEDED)"
echo "  import-response-annotations  (triggered by: assign-themes job SUCCEEDED)"
echo ""
echo "To trigger manually:"
echo "  make invoke-find-themes-lambda consultation_code=<code> run_date=<YYYY-MM-DD>"
echo "  make invoke-assign-themes-lambda consultation_code=<code> run_date=<YYYY-MM-DD>"
