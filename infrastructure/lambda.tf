
module "lambda" {
  #source         = "../../i-dot-ai-core-terraform-modules//modules/lambda" # For testing local changes
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=dk-add-job-role"

  file_path                      = "${path.root}/../pipeline-mapping/lambda_main.zip"
  handler                        = "lambda_main.lambda_handler"  
  runtime                        = "python3.9"
  function_name                  = "${local.name}-batch-lambda"
  package_type                   = "Zip"
  memory_size                    = 1024
  source_code_hash               = data.archive_file.consult_mapping_archive.output_base64sha256
  account_id                     = var.account_id
  lambda_additional_policy_arns  = {for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn}
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.batch_job_queue.arn
  function_name    = module.lambda.arn
  batch_size       = 1  # Adjust as needed
  enabled          = true
}
