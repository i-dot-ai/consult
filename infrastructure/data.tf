locals {
  record_prefix = var.env == "prod" ? var.project_name : "${var.project_name}-${var.env}"
  host          = terraform.workspace == "prod" ? "${var.project_name}.ai.cabinetoffice.gov.uk" : "${var.project_name}-${terraform.workspace}.ai.cabinetoffice.gov.uk"
  name          = "${var.team_name}-${var.env}-${var.project_name}"
  batch_memory        = 8192
  batch_vcpus         = 4
  ecs_memory    = var.env == "prod" ? 1024 : 512
  ecs_cpus      = var.env == "prod" ? 512 : 256

}

data "terraform_remote_state" "vpc" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "vpc/terraform.tfstate"
    region = var.region
  }
}


data "terraform_remote_state" "platform" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "platform/terraform.tfstate"
    region = var.region
  }
}


data "terraform_remote_state" "universal" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "universal/terraform.tfstate"
    region = var.region
  }
}


data "terraform_remote_state" "account" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "account/terraform.tfstate"
    region = var.region
  }
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}


data "aws_secretsmanager_secret" "env_vars" {
  name = "${local.name}-environment-variables"
}

data "aws_secretsmanager_secret_version" "env_vars" {
  secret_id = data.aws_secretsmanager_secret.env_vars.id
}

data "archive_file" "mapping_archive" {
  type        = "zip"
  source_file = "${path.root}/../pipeline-mapping/lambda/mapping.py"
  output_path = "${path.root}/../pipeline-mapping/lambda/mapping.zip"
}

data "archive_file" "slack_notifier_archive" {
  type        = "zip"
  source_file = "${path.root}/../pipeline-mapping/lambda/slack_notifier.py"
  output_path = "${path.root}/../pipeline-mapping/lambda/slack_notifier.zip"
}

data "aws_ssm_parameter" "slack_webhook_url" {
  name = "/i-dot-ai-${terraform.workspace}-consult/env_secrets/THEMEFINDER_SLACK_WEBHOOK_URL"
  depends_on = [
    aws_ssm_parameter.env_secrets  # Replace with your actual resource name
  ]
}
