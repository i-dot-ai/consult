module "load_balancer" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source           = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/load_balancer" # For testing local changes
  source          = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/load_balancer?ref=v2.0.1-load_balancer"
  name            = local.name
  account_id      = data.aws_caller_identity.current.account_id
  vpc_id          = data.terraform_remote_state.vpc.outputs.vpc_id
  public_subnets  = data.terraform_remote_state.vpc.outputs.public_subnets
  certificate_arn = module.acm_certificate.arn
  web_acl_arn     = module.waf.web_acl_arn
  env             = var.env
}

module "waf" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source        = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/waf" # For testing local changes
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/waf?ref=v7.1.1-waf"
  name   = local.name
  host   = local.host
  env    = var.env
}

resource "aws_route53_record" "type_a_record" {
  zone_id = data.aws_route53_zone.zone.zone_id
  name    = local.host
  type    = "A"

  alias {
    name                   = module.load_balancer.load_balancer_dns_name
    zone_id                = module.load_balancer.load_balancer_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "type_a_record_backend" {
  zone_id = data.aws_route53_zone.zone.zone_id
  name    = local.host_backend
  type    = "A"

  alias {
    name                   = module.load_balancer.load_balancer_dns_name
    zone_id                = module.load_balancer.load_balancer_zone_id
    evaluate_target_health = true
  }
}