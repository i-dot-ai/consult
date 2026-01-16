locals {
  backend_port  = 8000
  frontend_port = 3000

  base_env_vars = {
    "ENVIRONMENT" = terraform.workspace
    "DEBUG"       = var.env == "prod" ? false : true
    "GIT_SHA"     = var.image_tag
    "REPO"        = var.project_name
  }

  django_env_vars = {
    "LLM_GATEWAY_URL"                    = local.llm_gateway_url
    "DOMAIN_NAME"                        = local.host,
    "REDIS_HOST"                         = module.elasticache.redis_address
    "REDIS_PORT"                         = module.elasticache.redis_port
    "ASSIGN_THEMES_BATCH_JOB_NAME"       = "${local.name}-assign-themes-job"
    "ASSIGN_THEMES_BATCH_JOB_QUEUE"      = module.batch_job_mapping.job_queue_name
    "ASSIGN_THEMES_BATCH_JOB_DEFINITION" = module.batch_job_mapping.job_definition_name
    "FIND_THEMES_BATCH_JOB_NAME"         = "${local.name}-find-themes-job"
    "FIND_THEMES_BATCH_JOB_QUEUE"        = module.batch_job_sign_off.job_queue_name
    "FIND_THEMES_BATCH_JOB_DEFINITION"   = module.batch_job_sign_off.job_definition_name
    "AUTH_API_URL"                       = data.aws_ssm_parameter.auth_api_invoke_url.value
  }

  additional_policy_arns = { for idx, arn in [aws_iam_policy.ecs_exec_custom_policy.arn] : idx => arn }

}

module "backend" {
  name = "${local.name}-backend"
  # checkov:skip=CKV_SECRET_4:Skip secret check as these have to be used within the Github Action
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source                      = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source                        = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.8.0-ecs"
  image_tag                     = var.image_tag
  ecr_repository_uri            = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com/consult"
  vpc_id                        = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets               = data.terraform_remote_state.vpc.outputs.private_subnets
  host                          = local.host_backend
  public_host                   = var.edge_networking_enabled ? local.public_host_backend : null
  load_balancer_security_group  = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                    = module.load_balancer.alb_arn
  ecs_cluster_id                = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  ecs_cluster_name              = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  task_additional_iam_policies  = local.additional_policy_arns
  certificate_arn               = module.acm_certificate.arn
  target_group_name_override    = "consult-backend-${var.env}-tg"
  permissions_boundary_name     = "infra/i-dot-ai-${var.env}-consult-perms-boundary-app"
  https_listener_arn            = module.frontend.https_listener_arn
  service_discovery_service_arn = aws_service_discovery_service.service_discovery_service.arn
  create_networking             = false
  create_listener               = false

  additional_security_group_ingress = [
    {
      purpose          = "Frontend to backend container port"
      port             = local.backend_port
      additional_sg_id = module.frontend.ecs_sg_id
    }
  ]

  environment_variables = merge(local.base_env_vars, local.django_env_vars, {
    "APP_NAME"                 = var.project_name
    "EXECUTION_CONTEXT"        = "ecs"
    "DOCKER_BUILDER_CONTAINER" = "${var.project_name}-backend",
  })
  secrets = [
    for k, v in aws_ssm_parameter.env_secrets : {
      name      = regex("([^/]+$)", v.arn)[0], # Extract right-most string (param name) after the final slash
      valueFrom = v.arn
    }
  ]

  container_port = local.backend_port

  health_check = {
    accepted_response   = 200
    path                = "/"
    interval            = 60
    timeout             = 70
    healthy_threshold   = 2
    unhealthy_threshold = 5
    port                = local.backend_port
  }


  additional_execution_role_tags = {
    "RolePassableByRunner" = "True"
  }
  entrypoint = ["./start.sh"]

  memory = 4096
  cpu    = 1024

}

module "frontend" {
  name = "${local.name}-frontend"
  # checkov:skip=CKV_SECRET_4:Skip secret check as these have to be used within the Github Action
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source                      = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source                       = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.8.0-ecs"
  image_tag                    = var.image_tag
  ecr_repository_uri           = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com/consult-frontend"
  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  host                         = local.host
  public_host                  = var.edge_networking_enabled ? local.public_host : null
  load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                   = module.load_balancer.alb_arn
  ecs_cluster_id               = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  ecs_cluster_name             = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  create_listener              = true
  certificate_arn              = data.terraform_remote_state.universal.outputs.certificate_arn
  target_group_name_override   = "consult-frontend-${var.env}-tg"
  permissions_boundary_name    = "infra/i-dot-ai-${var.env}-consult-perms-boundary-app"

  environment_variables = combine(local.base_env_vars, {
    "PUBLIC_BACKEND_URL" = "http://${aws_service_discovery_service.service_discovery_service.name}.${aws_service_discovery_private_dns_namespace.private_dns_namespace.name}:${local.backend_port}",
  })
  container_port = local.frontend_port

  health_check = {
    accepted_response = 200

    interval            = 60
    timeout             = 70
    healthy_threshold   = 2
    unhealthy_threshold = 5
    port                = local.frontend_port
    path                = "/health"
  }

  authenticate_gds_internal_access = {
    enabled : true,
    client_id : aws_ssm_parameter.oidc_secrets["client_id"].value,
    client_secret : aws_ssm_parameter.oidc_secrets["client_secret"].value,
  }

  task_additional_iam_policies = local.additional_policy_arns
  entrypoint                   = ["npm", "start"]
}

module "worker" {
  name = "${local.name}-worker"
  # checkov:skip=CKV_SECRET_4:Skip secret check as these have to be used within the Github Action
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source                      = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source                       = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.8.0-ecs"
  image_tag                    = var.image_tag
  ecr_repository_uri           = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com/consult"
  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  host                         = local.host_backend
  public_host                  = var.edge_networking_enabled ? local.public_host_backend : null
  load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                   = module.load_balancer.alb_arn
  ecs_cluster_id               = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  ecs_cluster_name             = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  task_additional_iam_policies = local.additional_policy_arns
  certificate_arn              = module.acm_certificate.arn
  # target_group_name_override   = "consult-worker-${var.env}-tg"
  # permissions_boundary_name    = "infra/i-dot-ai-${var.env}-consult-perms-boundary-app"
  # https_listener_arn            = module.frontend.https_listener_arn
  # service_discovery_service_arn = aws_service_discovery_service.service_discovery_service.arn
  create_networking = false
  create_listener   = false



  environment_variables = merge(local.base_env_vars, local.django_env_vars)
  secrets = [
    for k, v in aws_ssm_parameter.env_secrets : {
      name      = regex("([^/]+$)", v.arn)[0], # Extract right-most string (param name) after the final slash
      valueFrom = v.arn
    }
  ]

  container_port = local.backend_port

  health_check = {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    accepted_response   = "200"
    path                = "/"
    timeout             = 6
    port                = 8000
  }

  autoscaling_maximum_target = 4

  additional_execution_role_tags = {
    "RolePassableByRunner" = "True"
  }
  entrypoint = ["./start-worker.sh"]

  memory = 4096
  cpu    = 1024
}

resource "aws_service_discovery_private_dns_namespace" "private_dns_namespace" {
  name        = "${local.name}-internal"
  description = "${local.name} private dns namespace"
  vpc         = data.terraform_remote_state.vpc.outputs.vpc_id
}

resource "aws_service_discovery_service" "service_discovery_service" {
  name = "${local.name}-backend"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.private_dns_namespace.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}


module "sns_topic" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                       = "../../i-dot-ai-core-terraform-modules/modules/observability/cloudwatch-slack-integration"
  source        = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/observability/cloudwatch-slack-integration?ref=v2.0.1-cloudwatch-slack-integration"
  name          = local.name
  slack_webhook = data.aws_secretsmanager_secret_version.platform_slack_webhook.secret_string

  permissions_boundary_name = "infra/i-dot-ai-${var.env}-consult-perms-boundary-app"
}

module "backend-ecs-alarm" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                       = "../../i-dot-ai-core-terraform-modules/modules/observability/ecs-alarms"
  source           = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/observability/ecs-alarms?ref=v1.0.1-ecs-alarms"
  name             = "${local.name}-backend"
  ecs_service_name = module.backend.ecs_service_name
  ecs_cluster_name = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  sns_topic_arn    = [module.sns_topic.sns_topic_arn]
}
module "frontend-ecs-alarm" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                       = "../../i-dot-ai-core-terraform-modules/modules/observability/ecs-alarms"
  source           = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/observability/ecs-alarms?ref=v1.0.1-ecs-alarms"
  name             = "${local.name}-frontend"
  ecs_service_name = module.frontend.ecs_service_name
  ecs_cluster_name = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  sns_topic_arn    = [module.sns_topic.sns_topic_arn]
}
module "backend-alb-alarm" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                       = "../../i-dot-ai-core-terraform-modules/modules/observability/alb-alarms"
  source        = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/observability/alb-alarms?ref=v1.1.0-alb-alarms"
  name          = "${local.name}-backend"
  alb_arn       = module.load_balancer.alb_arn
  target_group  = module.backend.aws_lb_target_group_name
  sns_topic_arn = [module.sns_topic.sns_topic_arn]
}
module "frontend-alb-alarm" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                       = "../../i-dot-ai-core-terraform-modules/modules/observability/alb-alarms"
  source        = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/observability/alb-alarms?ref=v1.1.0-alb-alarms"
  name          = "${local.name}-frontend"
  alb_arn       = module.load_balancer.alb_arn
  target_group  = module.frontend.aws_lb_target_group_name
  sns_topic_arn = [module.sns_topic.sns_topic_arn]
}
