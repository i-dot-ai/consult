module "elasticache" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source          = "../../i-ai-core-infrastructure//modules/elasticache"
  source          = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/elasticache?ref=v1.3.0-elasticache"
  name            = local.name
  vpc_id          = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets = data.terraform_remote_state.vpc.outputs.private_subnets
  security_group_ids = tomap(
    {
      "worker" = module.worker.ecs_sg_id
      "ecs"    = module.backend.ecs_sg_id
      "lambda" = aws_security_group.lambda_sg.id
    }
  )
}

module "elasticache_alarms" {
  source         = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/observability/elasticache-alarms?ref=v1.0.0-elasticache-alarms"
  name           = local.name
  sns_topic_arns = [module.sns_topic.sns_topic_arn]

  elasticache_metadata = {
    cache_cluster_id = module.elasticache.cluster_id
  }

  alarms_config = {
    # Redis backs the RQ queue, so any eviction is a dropped job (module default is 100).
    evictions_high = {
      threshold = 1
    }
    # Well below the node's ~65000 maxclients; catches a connection leak.
    connections_high = {
      threshold = 5000
    }
  }
}
