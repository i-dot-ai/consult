resource "aws_security_group" "lambda_sg" {
  name_prefix = "${local.name}-lambda-sg"
  vpc_id      = data.terraform_remote_state.vpc.outputs.vpc_id

  egress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [data.terraform_remote_state.vpc.outputs.vpc_cidr_block]
    description = "Redis access"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound for Slack notifications"
  }

  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "DNS queries"
  }
}

# -------------------------------------------------------------------
# slack_notifier — simple single-file Lambda (no dependencies)
# -------------------------------------------------------------------

data "archive_file" "slack_notifier_archive" {
  type        = "zip"
  source_dir  = "${path.root}/../build/slack_notifier"
  output_path = "${path.root}/../out/slack_notifier.zip"
}

module "slack_notifier_lambda" {
  #source         = "../../i-dot-ai-core-terraform-modules//modules/lambda" # For testing local changes
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.2.0-lambda"

  file_path                     = data.archive_file.slack_notifier_archive.output_path
  handler                       = "main.lambda_handler"
  runtime                       = "python3.12"
  function_name                 = "${local.name}-slack-notifier-lambda"
  package_type                  = "Zip"
  memory_size                   = 1024
  source_code_hash              = data.archive_file.slack_notifier_archive.output_base64sha256
  account_id                    = data.aws_caller_identity.current.account_id
  lambda_additional_policy_arns = { for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn }
  environment_variables = {
    "SLACK_WEBHOOK_URL" = data.aws_ssm_parameter.slack_webhook_url.value,
    "LAMBDA_AWS_REGION" = data.aws_region.current.id,
    "ENVIRONMENT"       = terraform.workspace,
    "AWS_BUCKET_NAME"   = module.app_bucket.id,
    "AWS_ACCOUNT_ID"    = data.aws_caller_identity.current.account_id
  }
}

# -------------------------------------------------------------------
# import_candidate_themes — Lambda with dependency layer
# -------------------------------------------------------------------

data "archive_file" "import_candidate_themes_archive" {
  type        = "zip"
  source_dir  = "${path.root}/../build/import_candidate_themes"
  output_path = "${path.root}/../out/import_candidate_themes.zip"
}

data "archive_file" "import_candidate_themes_layer" {
  type        = "zip"
  source_dir  = "${path.root}/../build/packages/import_candidate_themes"
  output_path = "${path.root}/../build/layers/import_candidate_themes.zip"
}

resource "aws_lambda_layer_version" "import_candidate_themes_dependencies" {
  filename                 = data.archive_file.import_candidate_themes_layer.output_path
  layer_name               = "${local.name}-import-candidate-themes-layer"
  description              = "Dependency layer for import_candidate_themes"
  source_code_hash         = data.archive_file.import_candidate_themes_layer.output_base64sha256
  compatible_runtimes      = ["python3.12"]
  compatible_architectures = ["x86_64"]
}

module "import_candidate_themes_lambda" {
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.2.0-lambda"

  file_path                     = data.archive_file.import_candidate_themes_archive.output_path
  handler                       = "main.lambda_handler"
  runtime                       = "python3.12"
  function_name                 = "${local.name}-import-candidate-themes-lambda"
  package_type                  = "Zip"
  memory_size                   = 1024
  source_code_hash              = data.archive_file.import_candidate_themes_archive.output_base64sha256
  account_id                    = data.aws_caller_identity.current.account_id
  lambda_additional_policy_arns = { for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn }
  layers                        = [aws_lambda_layer_version.import_candidate_themes_dependencies.arn]
  aws_security_group_ids        = [aws_security_group.lambda_sg.id]
  subnet_ids                    = data.terraform_remote_state.vpc.outputs.private_subnets
  environment_variables = {
    REDIS_HOST        = module.elasticache.redis_address
    REDIS_PORT        = module.elasticache.redis_port
    AWS_BUCKET_NAME   = module.app_bucket.id
    LAMBDA_AWS_REGION = data.aws_region.current.id
    AWS_ACCOUNT_ID    = data.aws_caller_identity.current.account_id
  }
}

# -------------------------------------------------------------------
# import_response_annotations — Lambda with dependency layer
# -------------------------------------------------------------------

data "archive_file" "import_response_annotations_archive" {
  type        = "zip"
  source_dir  = "${path.root}/../build/import_response_annotations"
  output_path = "${path.root}/../out/import_response_annotations.zip"
}

data "archive_file" "import_response_annotations_layer" {
  type        = "zip"
  source_dir  = "${path.root}/../build/packages/import_response_annotations"
  output_path = "${path.root}/../build/layers/import_response_annotations.zip"
}

resource "aws_lambda_layer_version" "import_response_annotations_dependencies" {
  filename                 = data.archive_file.import_response_annotations_layer.output_path
  layer_name               = "${local.name}-import-response-annotations-layer"
  description              = "Dependency layer for import_response_annotations"
  source_code_hash         = data.archive_file.import_response_annotations_layer.output_base64sha256
  compatible_runtimes      = ["python3.12"]
  compatible_architectures = ["x86_64"]
}

module "import_response_annotations_lambda" {
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.2.0-lambda"

  file_path                     = data.archive_file.import_response_annotations_archive.output_path
  handler                       = "main.lambda_handler"
  runtime                       = "python3.12"
  function_name                 = "${local.name}-import-response-annotations-lambda"
  package_type                  = "Zip"
  memory_size                   = 1024
  source_code_hash              = data.archive_file.import_response_annotations_archive.output_base64sha256
  account_id                    = data.aws_caller_identity.current.account_id
  lambda_additional_policy_arns = { for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn }
  layers                        = [aws_lambda_layer_version.import_response_annotations_dependencies.arn]
  aws_security_group_ids        = [aws_security_group.lambda_sg.id]
  subnet_ids                    = data.terraform_remote_state.vpc.outputs.private_subnets
  environment_variables = {
    REDIS_HOST        = module.elasticache.redis_address
    REDIS_PORT        = module.elasticache.redis_port
    AWS_BUCKET_NAME   = module.app_bucket.id
    LAMBDA_AWS_REGION = data.aws_region.current.id
    AWS_ACCOUNT_ID    = data.aws_caller_identity.current.account_id
  }
}
