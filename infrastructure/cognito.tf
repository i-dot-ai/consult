resource "aws_cognito_user" "this" {
  for_each     = toset(var.users)
  user_pool_id = module.cognito.user_pool_id
  username     = each.key

  desired_delivery_mediums = ["EMAIL"]
  temporary_password       = random_password.this[each.key].result
  attributes = {
    email          = each.key
    email_verified = true
  }
}

resource "random_password" "this" {
  for_each    = toset(var.users)
  length      = 16
  min_numeric = 1
  min_special = 1
  min_upper   = 1
  min_lower   = 1
  special     = true
}

module "cognito" {
  # checkov:skip=CKV_SECRET_4:Skip secret check as these have to be used within the Github Action
  source                    = "../../i-ai-core-infrastructure//modules/cognito"
  name                      = var.name
  invite_email_addition     = "Access the application at https://${var.record_prefix}.${var.domain_name}"
  invite_subject            = "${var.record_prefix} temporary credentials"
  record_prefix             = var.record_prefix
  identity_provider_enabled = false
  case_sensitive_username   = false
}
