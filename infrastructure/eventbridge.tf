resource "aws_cloudwatch_event_rule" "batch_job_state_change" {
  name        = "${local.name}-batch-job-state"
  description = "Capture AWS Batch job state changes"

   event_pattern = jsonencode({
    source      = ["aws.batch"],
    detail-type = ["Batch Job State Change"],
    detail = {
      status  = ["SUCCEEDED", "FAILED", "RUNNING"],
      jobName = ["${local.name}-mapping-job", "${local.name}-sign-off-job"]
    }
  })
  tags = var.universal_tags
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
        Action = [
          "lambda:InvokeFunction"
        ],
        Effect = "Allow",
        "Resource": [
                "arn:aws:lambda:${var.region}:${data.aws_caller_identity.current.account_id}:function:${local.name}-slack-notifier-lambda"
            ]
      }
    ]
  })
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.batch_job_state_change.name
  target_id = "SlackNotifierLambdaTarget"
  arn       = module.slack_notifier_lambda.arn
  role_arn  = aws_iam_role.eventbridge_invoke_role.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = module.slack_notifier_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.batch_job_state_change.arn
}