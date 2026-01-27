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

data "terraform_remote_state" "account" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "account/terraform.tfstate"
    region = data.aws_region.current.id
  }
}

data "terraform_remote_state" "keycloak" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "core/keycloak/keycloak/terraform.tfstate"
    region = data.aws_region.current.id
  }
}

locals {
  # name              = "${var.team_name}-${var.env}-${var.project_name}"
  hosted_zone_name = terraform.workspace == "prod" ? var.domain_name : "${terraform.workspace}.${var.domain_name}"
  # host              = terraform.workspace == "prod" ? "${var.project_name}.${var.domain_name}" : "${var.project_name}.${terraform.workspace}.${var.domain_name}"
  # host_backend      = terraform.workspace == "prod" ? "${var.project_name}-backend-external.${var.domain_name}" : "${var.project_name}-backend-external.${terraform.workspace}.${var.domain_name}" 

  record_prefix = var.env == "prod" ? var.project_name : "${var.project_name}-${var.env}"
  host          = terraform.workspace == "prod" ? "${var.project_name}.ai.cabinetoffice.gov.uk" : "${var.project_name}-${terraform.workspace}.ai.cabinetoffice.gov.uk"
  host_backend  = terraform.workspace == "prod" ? "${var.project_name}-backend-external.ai.cabinetoffice.gov.uk" : "${var.project_name}-backend-external-${terraform.workspace}.ai.cabinetoffice.gov.uk"
  name          = "${var.team_name}-${var.env}-${var.project_name}"
  batch_memory  = 8192
  batch_vcpus   = 4
  ecs_memory    = var.env == "prod" ? 4096 : 4096
  ecs_cpus      = var.env == "prod" ? 2048 : 1024

  public_host         = terraform.workspace == "prod" ? "${var.project_name}.i.ai.gov.uk" : "${var.project_name}.${terraform.workspace}.i.ai.gov.uk"
  public_host_backend = terraform.workspace == "prod" ? "${var.project_name}-backend-external.i.ai.gov.uk" : "${var.project_name}-backend-external.${terraform.workspace}.i.ai.gov.uk"
}

# data "aws_ssm_parameter" "auth_provider_public_key" {
#   name = "/i-dot-ai-${terraform.workspace}-core-keycloak/realm_public_key"
# }

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

# data "aws_secretsmanager_secret_version" "env_vars" {
#   secret_id = data.aws_secretsmanager_secret.env_vars.id
# }
#
# data "aws_secretsmanager_secret" "env_vars" {
#   name = "${local.name}-environment-variables"
# }

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
