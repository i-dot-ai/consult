resource "random_password" "django_pass" {
  length  = 24
  special = false
}

data "aws_secretsmanager_secret" "env_vars" {
  name = "${local.name}-environment-variables"
}

data "aws_secretsmanager_secret_version" "env_vars" {
  secret_id = data.aws_secretsmanager_secret.env_vars.id
}
