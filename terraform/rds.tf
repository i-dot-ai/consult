module "rds" {
  # source                                = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/rds"
  # For testing local changes
  source                 = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/rds?ref=v4.1.1-rds"
  db_name = "consultations" # DO NOT CHANGE THIS!
  kms_secrets_arn                       = data.terraform_remote_state.platform.outputs.kms_key_arn
  name                                  = local.name
  public_subnet_ids_list                = data.terraform_remote_state.vpc.outputs.public_subnets
  vpc_id                                = data.terraform_remote_state.vpc.outputs.vpc_id
  engine                                = "aurora-postgresql"
  engine_version                        = "16.8"
  family                                = null
  engine_mode                           = "provisioned"
  aurora_min_scaling                    = 2
  aurora_max_scaling                    = 8
  aurora_instance_count                 = 2
  deletion_protection                   = var.env == "dev" ? false : true
  env                                   = var.env
  rds_vpn_access_ips                    = data.aws_wafv2_ip_set.ip_whitelist_internal.addresses
  enable_performance_insights           = var.env == "dev" ? false : true
  performance_insights_retention_period = var.env == "dev" ? null : 7
  service_sg_ids = [
    module.backend.ecs_sg_id,
    module.worker.ecs_sg_id
  ]
}