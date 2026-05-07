module "rds" {
  # source                                = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/rds"
  source                                = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/rds?ref=v4.4.0-rds"
  db_name                               = "consultations" # DO NOT CHANGE THIS!
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

module "rds_alarms" {
  # source         = "../../i-dot-ai-core-terraform-modules//modules/observability/rds-alarms"
  source         = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/observability/rds-alarms?ref=v1.0.0-rds-alarms"
  name           = local.name
  sns_topic_arns = [module.sns_topic.sns_topic_arn]

  rds_metadata = {
    engine                 = module.rds.engine
    is_aurora              = module.rds.is_aurora
    db_instance_identifier = module.rds.db_instance_identifier
    db_cluster_identifier  = module.rds.db_cluster_identifier
    aurora_instance_count  = module.rds.aurora_instance_count
    storage_type           = module.rds.storage_type
  }

  alarms_config = {
    # ~10% of Aurora Serverless v2 min_capacity floor (2 ACU = 4 GiB).
    freeable_memory_low = {
      threshold = 429496729
    }
    # ~80% of Postgres default max_connections at 4 GiB (~450).
    database_connections_high = {
      threshold = 360
    }
  }
}
