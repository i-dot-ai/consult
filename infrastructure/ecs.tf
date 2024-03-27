locals {
  postgres_fqdn = "${module.postgres.rds_instance_username}:${module.postgres.rds_instance_db_password}@${module.postgres.db_instance_address}/${module.postgres.db_instance_name}"
}

module "ecs" {
  source             = "../../i-ai-core-infrastructure//modules/ecs"
  project_name       = var.project_name
  image_tag          = var.image_tag
  prefix             = "i-dot-ai"
  ecr_repository_uri = module.ecr.ecr_repository_url
  ecs_cluster_id     = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  health_check = {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    accepted_response   = "200"
    path                = "/"
    timeout             = 6
  }
  environment_variables = {
    "ENVIRONMENT"          = terraform.workspace,
    "DATABASE_URL"         = local.postgres_fqdn,
    "BATCH_JOB_QUEUE"      = module.batch_job_definition.job_queue_name,
    "BATCH_JOB_DEFINITION" = module.batch_job_definition.job_definition_name,
    "DJANGO_SECRET_KEY"    = data.aws_secretsmanager_secret_version.django_secret.secret_string
  }

  state_bucket                 = var.state_bucket
  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  container_port               = "80"
  load_balancer_security_group = data.terraform_remote_state.platform.outputs.load_balancer_security_group_id["default"]
  aws_lb_arn                   = data.terraform_remote_state.platform.outputs.load_balancer_arn["default"]
  host                         = local.host
  route53_record_name          = aws_route53_record.type_a_record.name

  authenticate_cognito = {
    enabled : true,
    user_pool_arn : module.cognito.user_pool_arn,
    user_pool_client_id : module.cognito.user_pool_client_id,
    user_pool_domain : module.cognito.user_pool_domain
  }
}


resource "aws_route53_record" "type_a_record" {
  zone_id = var.hosted_zone_id
  name    = local.host
  type    = "A"

  alias {
    name                   = data.terraform_remote_state.platform.outputs.dns_name["default"]
    zone_id                = data.terraform_remote_state.platform.outputs.zone_id["default"]
    evaluate_target_health = true
  }
}

resource "aws_secretsmanager_secret" "django_secret" {
  name        = "${var.prefix}-${var.project_name}-${var.env}-django-secret"
  description = "Django secret for ${var.project_name}"
}

data "aws_secretsmanager_secret_version" "django_secret" {
  secret_id  = aws_secretsmanager_secret.django_secret.id
  depends_on = [aws_secretsmanager_secret.django_secret]
}
