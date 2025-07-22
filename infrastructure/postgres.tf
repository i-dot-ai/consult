module "rds" {
    # source = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/rds"  # For testing local changes
  source                 = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/rds?ref=v3.4.0-rds"
  db_name                = "consultations"
  kms_secrets_arn        = data.terraform_remote_state.platform.outputs.kms_key_arn
  name                   = local.name
  public_subnet_ids_list = data.terraform_remote_state.vpc.outputs.public_subnets
  securelist_ips = toset(var.developer_ips)
  service_sg_ids = [
    module.ecs.ecs_sg_id,
    module.worker.ecs_sg_id
  ]
  vpc_id                 = data.terraform_remote_state.vpc.outputs.vpc_id
  engine                 = "aurora-postgresql"
  engine_version         = "16.6"
  family                 = null
  engine_mode            = "provisioned"
  aurora_min_scaling     = 2
  aurora_max_scaling     = 8
  aurora_instance_count  = 1
  deletion_protection    = var.env == "dev" ? false : true
}
