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

data "archive_file" "slack_notifier_archive" {
  type        = "zip"
  source_file = "${path.root}/../lambda/slack_notifier.py"
  output_path = "${path.root}/../lambda/slack_notifier.zip"
}

resource "null_resource" "build_import_candidate_themes_lambda" {
  triggers = {
    requirements = filemd5("${path.root}/../lambda/import_candidate_themes/requirements.txt")
    lambda_code  = filemd5("${path.root}/../lambda/import_candidate_themes/import_candidate_themes_handler.py")
  }

  provisioner "local-exec" {
    command = <<EOF
      # Create temporary build directory
      rm -rf ${path.root}/../lambda/import_candidate_themes/build
      mkdir -p ${path.root}/../lambda/import_candidate_themes/build

      # Copy source files to build directory
      cp ${path.root}/../lambda/import_candidate_themes/*.py ${path.root}/../lambda/import_candidate_themes/build/
      cp ${path.root}/../lambda/import_candidate_themes/requirements.txt ${path.root}/../lambda/import_candidate_themes/build/

      # Install dependencies in build directory with specific options
      cd ${path.root}/../lambda/import_candidate_themes/build
      pip install -r requirements.txt -t . --no-cache-dir --platform linux_x86_64 --only-binary=:all:

      # Verify packages were installed
      echo "Installed packages:"
      ls -la | grep -E "(redis|rq)"
    EOF
  }
}

data "archive_file" "import_candidate_themes_archive" {
  depends_on  = [null_resource.build_import_candidate_themes_lambda]
  type        = "zip"
  source_dir  = "${path.root}/../lambda/import_candidate_themes/build"
  output_path = "${path.root}/../lambda/import_candidate_themes.zip"
}

resource "null_resource" "build_import_response_annotations_lambda" {
  triggers = {
    requirements = filemd5("${path.root}/../lambda/import_response_annotations/requirements.txt")
    lambda_code  = filemd5("${path.root}/../lambda/import_response_annotations/import_response_annotations_handler.py")
  }

  provisioner "local-exec" {
    command = <<EOF
      # Create temporary build directory
      rm -rf ${path.root}/../lambda/import_response_annotations/build
      mkdir -p ${path.root}/../lambda/import_response_annotations/build

      # Copy source files to build directory
      cp ${path.root}/../lambda/import_response_annotations/*.py ${path.root}/../lambda/import_response_annotations/build/
      cp ${path.root}/../lambda/import_response_annotations/requirements.txt ${path.root}/../lambda/import_response_annotations/build/

      # Install dependencies in build directory with specific options
      cd ${path.root}/../lambda/import_response_annotations/build
      pip install -r requirements.txt -t . --no-cache-dir --platform linux_x86_64 --only-binary=:all:

      # Verify packages were installed
      echo "Installed packages:"
      ls -la | grep -E "(redis|rq)"
    EOF
  }
}

data "archive_file" "import_response_annotations_archive" {
  depends_on  = [null_resource.build_import_response_annotations_lambda]
  type        = "zip"
  source_dir  = "${path.root}/../lambda/import_response_annotations/build"
  output_path = "${path.root}/../lambda/import_response_annotations.zip"
}

module "slack_notifier_lambda" {
  #source         = "../../i-dot-ai-core-terraform-modules//modules/lambda" # For testing local changes
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.2.0-lambda"

  file_path                     = "${path.root}/../lambda/slack_notifier.zip"
  handler                       = "slack_notifier.lambda_handler"
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

module "import_response_annotations_lambda" {
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.2.0-lambda"

  file_path                     = "${path.root}/../lambda/import_response_annotations.zip"
  handler                       = "import_response_annotations_handler.lambda_handler"
  runtime                       = "python3.12"
  function_name                 = "${local.name}-import-response-annotations-lambda"
  package_type                  = "Zip"
  memory_size                   = 1024
  source_code_hash              = data.archive_file.import_response_annotations_archive.output_base64sha256
  account_id                    = data.aws_caller_identity.current.account_id
  lambda_additional_policy_arns = { for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn }
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

module "import_candidate_themes_lambda" {
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/lambda?ref=v2.2.0-lambda"

  file_path                     = "${path.root}/../lambda/import_candidate_themes.zip"
  handler                       = "import_candidate_themes_handler.lambda_handler"
  runtime                       = "python3.12"
  function_name                 = "${local.name}-import-candidate-themes-lambda"
  package_type                  = "Zip"
  memory_size                   = 1024
  source_code_hash              = data.archive_file.import_candidate_themes_archive.output_base64sha256
  account_id                    = data.aws_caller_identity.current.account_id
  lambda_additional_policy_arns = { for idx, arn in [aws_iam_policy.lambda_exec_custom_policy.arn] : idx => arn }
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
