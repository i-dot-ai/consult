
resource "aws_secretsmanager_secret" "django_secret" {
  name        = "${var.prefix}-${var.project_name}-${var.env}-django-secret"
  description = "Django secret for ${var.project_name}"
  tags = {
    SecretPurpose = "general" # pragma: allowlist secret
  }
}

data "aws_secretsmanager_secret" "django_secret" {
  arn = aws_secretsmanager_secret.django_secret.arn
}


data "aws_secretsmanager_secret_version" "django_secret" {
  secret_id = data.aws_secretsmanager_secret.django_secret.id
}

resource "aws_secretsmanager_secret" "django_debug" {
  name        = "${var.prefix}-${var.project_name}-${var.env}-django-debug"
  description = "Django secret for ${var.project_name}"
  tags = {
    SecretPurpose = "general" # pragma: allowlist secret
  }
}

data "aws_secretsmanager_secret" "django_debug" {
  arn = aws_secretsmanager_secret.django_debug.arn
}


data "aws_secretsmanager_secret_version" "django_debug" {
  secret_id = data.aws_secretsmanager_secret.django_debug.id
}