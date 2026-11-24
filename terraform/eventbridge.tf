resource "aws_cloudwatch_event_rule" "batch_job_import_response_annotations" {
  name        = "${local.name}-import-response-annotations"
  description = "Trigger response annotations import when assign themes batch job succeeds"

  event_pattern = jsonencode({
    source      = ["aws.batch"],
    detail-type = ["Batch Job State Change"],
    detail = {
      status  = ["SUCCEEDED"],
      jobName = ["${local.name}-assign-themes-job"]
    }
  })
  tags = var.universal_tags
}

resource "aws_cloudwatch_event_rule" "batch_job_state_change" {
  name        = "${local.name}-batch-job-state"
  description = "Capture AWS Batch job state changes for notifications"

  event_pattern = jsonencode({
    source      = ["aws.batch"],
    detail-type = ["Batch Job State Change"],
    detail = {
      status  = ["SUCCEEDED", "FAILED", "RUNNING"],
      jobName = ["${local.name}-assign-themes-job"]
    }
  })
  tags = var.universal_tags
}

resource "aws_cloudwatch_event_rule" "find_themes_worker_state_change" {
  name        = "${local.name}-find-themes-worker-state"
  description = "Capture find-themes worker state changes for notifications"

  event_pattern = jsonencode({
    source      = ["consult.worker"]
    detail-type = ["Find Themes Job State Change"]
  })
  tags = var.universal_tags
}

resource "aws_cloudwatch_event_target" "find_themes_slack_lambda_target" {
  rule      = aws_cloudwatch_event_rule.find_themes_worker_state_change.name
  target_id = "FindThemesSlackNotifierLambdaTarget"
  arn       = module.slack_notifier_lambda.arn
  role_arn  = aws_iam_role.eventbridge_invoke_role.arn
}

resource "aws_cloudwatch_event_target" "slack_lambda_target" {
  rule      = aws_cloudwatch_event_rule.batch_job_state_change.name
  target_id = "SlackNotifierLambdaTarget"
  arn       = module.slack_notifier_lambda.arn
  role_arn  = aws_iam_role.eventbridge_invoke_role.arn
}

resource "aws_cloudwatch_event_target" "import_response_annotations_target" {
  rule      = aws_cloudwatch_event_rule.batch_job_import_response_annotations.name
  target_id = "ImportResponseAnnotationsLambdaTarget"
  arn       = module.import_response_annotations_lambda.arn
  role_arn  = aws_iam_role.eventbridge_invoke_role.arn
}

resource "aws_lambda_permission" "allow_eventbridge_slack" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = module.slack_notifier_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.batch_job_state_change.arn
}

resource "aws_lambda_permission" "allow_eventbridge_find_themes_slack" {
  statement_id  = "AllowExecutionFromEventBridgeFindThemes"
  action        = "lambda:InvokeFunction"
  function_name = module.slack_notifier_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.find_themes_worker_state_change.arn
}

resource "aws_lambda_permission" "allow_eventbridge_import_response_annotations" {
  statement_id  = "AllowExecutionFromEventBridgeImportResponseAnnotations"
  action        = "lambda:InvokeFunction"
  function_name = module.import_response_annotations_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.batch_job_import_response_annotations.arn
}

resource "aws_iam_role" "eventbridge_invoke_role" {
  name = "${local.name}-eventbridge-invoke-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "${local.name}-eventbridge-policy"
  role = aws_iam_role.eventbridge_invoke_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "lambda:InvokeFunction"
        ],
        Resource = [
          module.slack_notifier_lambda.arn,
          module.import_response_annotations_lambda.arn
        ]
      }
    ]
  })
}
