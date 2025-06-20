module "load_balancer" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source         = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/load_balancer" # For testing local changes
  source          = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/load_balancer?ref=v1.3.0-load_balancer"
  name            = local.name
  account_id      = var.account_id
  vpc_id          = data.terraform_remote_state.vpc.outputs.vpc_id
  public_subnets  = data.terraform_remote_state.vpc.outputs.public_subnets
  ip_whitelist = concat(var.internal_ips, var.developer_ips, var.external_ips)
  certificate_arn = data.terraform_remote_state.universal.outputs.certificate_arn
  web_acl_arn     = module.waf.web_acl_arn
}

module "waf" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source        = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/waf" # For testing local changes
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/waf?ref=v5.3.0-waf"
  name   = local.name
  ip_set = concat(var.internal_ips, var.developer_ips, var.external_ips)
  scope  = var.scope
  host   = local.host
}

resource "aws_route53_record" "type_a_record" {
  zone_id = var.hosted_zone_id
  name    = local.host
  type    = "A"

  alias {
    name                   = module.load_balancer.load_balancer_dns_name
    zone_id                = module.load_balancer.load_balancer_zone_id
    evaluate_target_health = true
  }
}
