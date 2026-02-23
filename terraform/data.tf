data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "terraform_remote_state" "vpc" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "vpc/terraform.tfstate"
    region = data.aws_region.current.id
  }
}

data "terraform_remote_state" "platform" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "platform/terraform.tfstate"
    region = data.aws_region.current.id
  }
}

data "terraform_remote_state" "universal" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "universal/terraform.tfstate"
    region = data.aws_region.current.id
  }
}

locals {
  record_prefix            = var.env == "prod" ? var.project_name : "${var.project_name}-${var.env}"
  host                     = terraform.workspace == "prod" ? "${var.project_name}.ai.cabinetoffice.gov.uk" :
    "${var.project_name}-${terraform.workspace}.ai.cabinetoffice.gov.uk"
  host_backend             = terraform.workspace == "prod" ?
    "${var.project_name}-backend-external.ai.cabinetoffice.gov.uk" :
    "${var.project_name}-backend-external-${terraform.workspace}.ai.cabinetoffice.gov.uk"
  public_host              = terraform.workspace == "prod" ? "${var.project_name}.i.ai.gov.uk" :
    "${var.project_name}.${terraform.workspace}.i.ai.gov.uk"
  name                     = "${var.team_name}-${var.env}-${var.project_name}"
  batch_mapping_image_url  = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.id}.amazonaws.com/consult-pipeline-mapping:${var.image_tag}"
  batch_sign_off_image_url = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.id}.amazonaws.com/consult-pipeline-sign-off:${var.image_tag}"
  llm_gateway_url          = "https://llm-gateway.i.ai.gov.uk/"
}

data "aws_ssm_parameter" "auth_api_invoke_url" {
  name = "/i-dot-ai-${terraform.workspace}-core-auth-api/auth/INVOKE_URL"
}

data "aws_secretsmanager_secret" "slack" {
  name = "i-dot-ai-${var.env}-platform-slack-webhook"
}

data "aws_secretsmanager_secret_version" "platform_slack_webhook" {
  secret_id = data.aws_secretsmanager_secret.slack.id
}

data "aws_wafv2_ip_set" "ip_whitelist_internal" {
  name  = "i-dot-ai-core-ip-config-ip-set-internal"
  scope = var.scope
}

data "aws_route53_zone" "zone" {
  name = "ai.cabinetoffice.gov.uk"
}


data "aws_ssm_parameter" "slack_webhook_url" {
  name = "/i-dot-ai-${terraform.workspace}-consult/env_secrets/THEMEFINDER_SLACK_WEBHOOK_URL"
  depends_on = [
    aws_ssm_parameter.env_secrets
  ]
}

data "aws_ssm_parameter" "litellm_api_key" {
  name = "/i-dot-ai-prod-core-llm-gateway/env_secrets/${var.project_name}/${var.env}-key-api-key"
}

data "aws_ssm_parameter" "edge_secret" {
  name = "/i-dot-ai-${terraform.workspace}-core-edge-network/header-secret"
}
