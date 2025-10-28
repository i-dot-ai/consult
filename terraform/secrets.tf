resource "random_password" "django_pass" {
  length  = 24
  special = false
}


locals {
  # Add secrets to this list as required to make them available within the container.
  # Values must not be hardcoded here - they must either be references or updated in SSM Parameter Store.
  env_secrets = [
    {
      name  = "DATA_S3_BUCKET"
      value = module.app_bucket.id
    },
    {
      name  = "AWS_REGION"
      value = var.region
    },
    {
      name  = "THEMEFINDER_SLACK_WEBHOOK_URL"
      value = "placeholder" # Update value in SSM - Do not hardcode
    },
    {
      name  = "LITELLM_CONSULT_OPENAI_API_KEY"
      value = data.aws_ssm_parameter.litellm_api_key.value
    }
  ]
}

resource "aws_ssm_parameter" "env_secrets" {
  for_each = { for ev in local.env_secrets : ev.name => ev }
  
  type   = "SecureString"
  key_id = data.terraform_remote_state.platform.outputs.kms_key_arn

  name  = "/${local.name}/env_secrets/${each.value.name}"
  value = each.value.value

  lifecycle {
    ignore_changes = [
      value,
    ]
  }
}
