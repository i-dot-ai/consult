module "submit_batch_job_lambda" {
  #source         = "../../i-dot-ai-core-terraform-modules//modules/lambda" # For testing local changes
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.0.1-lambda"

  file_path                      = "${path.root}/../lambda/submit_batch_job.zip"
  handler                        = "submit_batch_job.lambda_handler"  
  runtime                        = "python3.12"
  function_name                  = "${local.name}-submit-batch-job-lambda"
  package_type                   = "Zip"
  memory_size                    = 1024
  source_code_hash               = data.archive_file.submit_batch_job_archive.output_base64sha256
  account_id                     = var.account_id
  lambda_additional_policy_arns  = {for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn}
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = module.batch_job_queue.sqs_queue_arn
  function_name    = module.submit_batch_job_lambda.arn
  batch_size       = 1  
  enabled          = true
}


module "slack_notifier_lambda" {
  #source         = "../../i-dot-ai-core-terraform-modules//modules/lambda" # For testing local changes
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.0.1-lambda"

  file_path                      = "${path.root}/../lambda/slack_notifier.zip"
  handler                        = "slack_notifier.lambda_handler"  
  runtime                        = "python3.12"
  function_name                  = "${local.name}-slack-notifier-lambda"
  package_type                   = "Zip"
  memory_size                    = 1024
  source_code_hash               = data.archive_file.slack_notifier_archive.output_base64sha256
  account_id                     = var.account_id
  lambda_additional_policy_arns  = {for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn}
  environment_variables = {
    "SLACK_WEBHOOK_URL" = data.aws_ssm_parameter.slack_webhook_url.value,
    "LAMBDA_AWS_REGION" = local.secret_env_vars.AWS_REGION,
  }
}
