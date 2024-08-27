module "rds" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
#  source = "../../../i-dot-ai-core-terraform-modules//modules/infrastructure/rds"  # For testing local changes
  source                  = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/rds?ref=v1.0.0-rds"
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  public_subnet_ids_list  = data.terraform_remote_state.vpc.outputs.public_subnets
  private_subnet_ids_list = data.terraform_remote_state.vpc.outputs.private_subnets
  instance_type           = "db.t3.large"
  db_name                 = var.project_name
  kms_secrets_arn         = data.terraform_remote_state.platform.outputs.kms_key_arn
  name                    = local.name
  domain_name             = var.domain_name
  state_bucket            = var.state_bucket
  service_sg_ids          = [module.ecs.ecs_sg_id]
  publicly_accessible     = var.publicly_accessible
  securelist_ips          = concat(var.developer_ips, var.internal_ips)
  secret_tags             = {
    "platform:secret-purpose" : "general"
  }
}
