module "elasticache" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source          = "../../i-ai-core-infrastructure//modules/elasticache"
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/elasticache?ref=v1.0.0-elasticache"
  name            = local.name
  vpc_id          = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets = data.terraform_remote_state.vpc.outputs.private_subnets
  security_group_ids = tomap(
    {
      "worker"   = module.worker.ecs_sg_id
      "ecs"      = module.ecs.ecs_sg_id
    }
  )
}
