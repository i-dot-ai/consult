# resource "aws_secretsmanager_secret" "django_secret" {
#   name        = "${local.name}-django-secret"
#   description = "Django secret for ${local.name}"
#   tags = {
#     "platform:secret-purpose" : "general" # pragma: allowlist secret
#   }
# }
#
# resource "aws_secretsmanager_secret_version" "django-app-json-secret" {
#   secret_id     = aws_secretsmanager_secret.django_secret.id
#   secret_string = random_password.django_pass.result
# }

resource "random_password" "django_pass" {
  length  = 24
  special = false
}

# data "aws_secretsmanager_secret" "django_secret" {
#   name = aws_secretsmanager_secret.django_secret.name
#   depends_on = [aws_secretsmanager_secret.django_secret]
# }
#
# data "aws_secretsmanager_secret_version" "django_secret" {
#   secret_id = data.aws_secretsmanager_secret.django_secret.id
# }

data "aws_secretsmanager_secret" "env_vars" {
  name = "${local.name}-environment-variables"
}

data "aws_secretsmanager_secret_version" "env_vars" {
  secret_id = data.aws_secretsmanager_secret.env_vars.id
}
