data "aws_vpc" "vpc" {
  id = var.vpc_id
}

module "postgres" {
  source                  = "../../modules/postgres"
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  public_subnet_ids_list  = data.terraform_remote_state.vpc.outputs.public_subnets
  private_subnet_ids_list = data.terraform_remote_state.vpc.outputs.private_subnets
  aws_project             = var.project
  instance_type           = "db.t3.large"
  developer_ips           = var.developer_ips
  db_name                 = local.name
  kms_secrets_arn         = data.terraform_remote_state.universal.outputs.kms_secrets_arn
  service_sg_id           = var.service_sg_id
  project                 = local.name
  domain_name             = data.terraform_remote_state.account.outputs.domain_name
}
