data "aws_iam_policy_document" "ecs_exec_custom_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:Get*",
      "s3:List*",
      "s3:Put*",
      "s3:Delete*",
    ]
    resources = [
      "${module.app_bucket.arn}/app_data/*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:Get*",
      "s3:List*",
    ]
    resources = [
      module.app_bucket.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
    ]
    resources = [
      "arn:aws:ssm:*:${data.aws_caller_identity.current.account_id}:parameter/${local.name}/env_secrets/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey",
    ]
    resources = [
      data.terraform_remote_state.platform.outputs.kms_key_arn,
    ]
  }
}

resource "aws_iam_policy" "ecs_exec_custom_policy" {
  name        = "${local.name}-ecs-custom-exec"
  description = "ECS task custom policy"
  policy      = data.aws_iam_policy_document.ecs_exec_custom_policy.json
}



data "aws_iam_policy_document" "lambda_exec_custom_policy" {
  statement {
    effect = "Allow"
    actions = [
      "batch:Submit*",
      "batch:Describe*",
    ]
    resources = [
          "arn:aws:batch:${var.region}:${data.aws_caller_identity.current.account_id}:job-queue/i-dot-ai-dev-consult-mapping*",
          "arn:aws:batch:${var.region}:${data.aws_caller_identity.current.account_id}:job-definition/i-dot-ai-dev-consult-mapping*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
    ]
    resources = [aws_sqs_queue.batch_job_queue.arn]
  }
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey"
    ]
    resources = [
      data.terraform_remote_state.platform.outputs.kms_key_arn
    ]
  }
  
}

resource "aws_iam_policy" "lambda_exec_custom_policy" {
  name        = "${local.name}-batch-lambda-policy"
  description = "lambda custom policy"
  policy      = data.aws_iam_policy_document.lambda_exec_custom_policy.json
}
