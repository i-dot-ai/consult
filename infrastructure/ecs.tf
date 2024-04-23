locals {
  postgres_fqdn = "${module.postgres.rds_instance_username}:${module.postgres.rds_instance_db_password}@${module.postgres.db_instance_address}/${module.postgres.db_instance_name}"
}

module "ecs" {
  source             = "../../i-ai-core-infrastructure//modules/ecs"
  project_name       = var.project_name
  image_tag          = var.image_tag
  prefix             = "i-dot-ai"
  ecr_repository_uri = var.ecr_repository_uri
  ecs_cluster_id     = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  health_check = {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    accepted_response   = "200"
    path                = "/"
    timeout             = 6
    port                = 8000
  }
  environment_variables = {
    "ENVIRONMENT"           = terraform.workspace,
    "PRODUCTION_DEPLOYMENT" = true,
    "BATCH_JOB_QUEUE"       = module.batch_job_definition.job_queue_name,
    "BATCH_JOB_DEFINITION"  = module.batch_job_definition.job_definition_name,
    "DJANGO_SECRET_KEY"     = data.aws_secretsmanager_secret_version.django_secret.secret_string
    "DB_NAME" : "${module.postgres.db_instance_name}",
    "DB_USER" : "${module.postgres.rds_instance_username}",
    "DB_PASSWORD" : "${module.postgres.rds_instance_db_password}",
    "DB_HOST" : "${module.postgres.db_instance_address}",
    "DOMAIN_NAME" : "${local.host}"
  }

  state_bucket                 = var.state_bucket
  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  container_port               = "8000"
  load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                   = module.load_balancer.alb_arn
  host                         = local.host
  route53_record_name          = aws_route53_record.type_a_record.name
  ip_whitelist                 = var.external_ips
  create_networking            = true
  create_listener              = true
}


resource "aws_route53_record" "type_a_record" {
  zone_id = var.hosted_zone_id
  name    = local.host
  type    = "A"

  alias {
    name                   = module.load_balancer.load_balancer_dns_name
    zone_id                = module.load_balancer.load_balancer_zone_id
    evaluate_target_health = true
  }
}
