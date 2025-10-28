module "app_bucket" {
  # checkov:skip=CKV_SECRET_4:Skip secret check as these have to be used within the Github Action
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source        = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/s3" # For testing local changes
  source        = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/s3?ref=v3.0.0-s3"
  name          = "${local.name}-data"
  log_bucket    = data.terraform_remote_state.platform.outputs.log_bucket
  kms_key       = data.terraform_remote_state.platform.outputs.kms_key_arn
  force_destroy = var.env == "dev" ? true : false
  # source_ips   = concat(var.internal_ips, var.developer_ips)
}
