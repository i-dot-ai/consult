module "acm_certificate" {
  # checkov:skip=CKV_TF_1: Internal repo - we're using semantic versions instead of commit hash
  #  source = "../../../i-dot-ai-core-terraform-modules//modules/infrastructure/acm"  # For testing local changes
  source            = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/acm?ref=v3.0.0-acm"
  domain_name       = local.host
  validation_method = "DNS"
  hosted_zone_id    = data.aws_route53_zone.zone.id

  subject_alternative_names = [
    local.host_backend,
  ]
}
	