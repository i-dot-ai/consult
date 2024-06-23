module "app_bucket" {
  # checkov:skip=CKV_SECRET_4:Skip secret check as these have to be used within the Github Action
  name           = "${local.name}-data"
  source         = "../../i-ai-core-infrastructure//modules/s3"
  state_bucket   = var.state_bucket
  log_bucket     = data.terraform_remote_state.platform.outputs.log_bucket
  kms_key        = data.terraform_remote_state.platform.outputs.kms_key_arn
  source_ips     = concat(var.internal_ips, var.developer_ips, var.external_ips)
}