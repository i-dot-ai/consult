module "ecs" {
  source             = "../../modules/ecs"
  project_name       = local.name
  image_tag          = var.image_tag
  prefix             = var.prefix
  ecr_repository_uri = var.ecr_repository_uri
  cluster_name       = var.cluster_name

  state_bucket                 = var.state_bucket
  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  container_port               = var.container_port
  load_balancer_security_group = data.terraform_remote_state.platform.outputs.load_balancer_security_group_id["default"]
  aws_lb_arn                   = data.terraform_remote_state.platform.outputs.load_balancer_arn["default"]
}
