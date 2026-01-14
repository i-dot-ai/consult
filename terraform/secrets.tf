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
      name  = "SENTRY_DSN"
      value = "placeholder" # Update value in SSM - Do not hardcode - Empty value will disable sentry
    },
    {
      name  = "POSTGRES_PORT"
      value = 5432
    },
    {
      name  = "POSTGRES_DB"
      value = module.rds.db_instance_name
    },
    {
      name  = "POSTGRES_USER"
      value = module.rds.rds_instance_username
    },
    {
      name  = "POSTGRES_PASSWORD"
      value = module.rds.rds_instance_db_password
    },
    {
      name  = "POSTGRES_HOST"
      value = module.rds.db_instance_address
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
    },
    {
      name  = "DJANGO_SECRET_KEY"
      value = random_password.django_pass.result
    },
    {
      name  = "AUTH_API_URL"
      value = data.aws_ssm_parameter.auth_api_invoke_url.value
    },
    {
      name  = "AWS_BUCKET_NAME"
      value = "${var.team_name}-${var.env}-${var.project_name}-data"
    },
    {
      name  = "DATABASE_URL"
      value = "postgres://${module.rds.rds_instance_username}:${module.rds.rds_instance_db_password}@${module.rds.db_instance_address}/${module.rds.db_instance_name}"
    },
    {
      name  = "GUNICORN_WORKERS"
      value = "placeholder"
    },
    {
      name  = "GUNICORN_TIMEOUT"
      value = "placeholder"
    },
    {
      name  = "ADMIN_USERS"
      value = "placeholder"
    },
    {
      name  = "ADMIN_USERS"
      value = "placeholder"
    },
    {
      name  = "PUBLIC_INTERNAL_ACCESS_CLIENT_ID"
      value = aws_ssm_parameter.oidc_secrets["client_id"].value,
    }
  ]

  # These settings are used by the platform team to configure authentication into the application.
  oidc_secrets = [
    {
      name  = "client_id"
      value = "placeholder" # Update value in SSM - Do not hardcode
    },
    {
      name  = "client_secret"
      value = "placeholder" # Update value in SSM - Do not hardcode
    },
  ]
}

resource "aws_ssm_parameter" "oidc_secrets" {
  for_each = { for os in local.oidc_secrets : os.name => os }

  type   = "SecureString"
  key_id = data.terraform_remote_state.platform.outputs.kms_key_arn

  name  = "/${local.name}/oidc_secrets/${each.value.name}"
  value = each.value.value

  lifecycle {
    ignore_changes = [
      value,
    ]
  }
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
