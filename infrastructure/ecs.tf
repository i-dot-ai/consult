locals {
  rds_fqdn        = "postgres://${module.rds.rds_instance_username}:${module.rds.rds_instance_db_password}@${module.rds.db_instance_address}/${module.rds.db_instance_name}"
  secret_env_vars = jsondecode(data.aws_secretsmanager_secret_version.env_vars.secret_string)
  base_env_vars = {
    "ENVIRONMENT"                          = terraform.workspace,
    "DJANGO_SECRET_KEY"                    = random_password.django_pass.result,
    "DEBUG"                                = local.secret_env_vars.DEBUG,
    "GOVUK_NOTIFY_API_KEY"                 = local.secret_env_vars.GOVUK_NOTIFY_API_KEY,
    "GOVUK_NOTIFY_PLAIN_EMAIL_TEMPLATE_ID" = local.secret_env_vars.GOVUK_NOTIFY_PLAIN_EMAIL_TEMPLATE_ID,
    "SENTRY_DSN"                           = local.secret_env_vars.SENTRY_DSN,
    "AWS_REGION"                           = local.secret_env_vars.AWS_REGION,
    "AWS_BUCKET_NAME"                      = local.secret_env_vars.AWS_BUCKET_NAME,
    "DATABASE_URL"                         = local.rds_fqdn,
    "DOMAIN_NAME"                          = "${local.host}",
    "GIT_SHA"                              = var.image_tag,
    "APP_BUCKET"                           = local.secret_env_vars.APP_BUCKET,
    "GUNICORN_WORKERS"                     = local.secret_env_vars.GUNICORN_WORKERS,
    "GUNICORN_TIMEOUT"                     = local.secret_env_vars.GUNICORN_TIMEOUT,
    "ADMIN_USERS"                          = local.secret_env_vars.ADMIN_USERS,
    "AZURE_OPENAI_API_KEY"                 = local.secret_env_vars.AZURE_OPENAI_API_KEY,
    "OPENAI_API_VERSION"                   = local.secret_env_vars.OPENAI_API_VERSION,
    "AZURE_OPENAI_ENDPOINT"                = local.secret_env_vars.AZURE_OPENAI_ENDPOINT,
    "BACKEND_URL"                          = "http://${aws_service_discovery_service.service_discovery_service.name}.${aws_service_discovery_private_dns_namespace.private_dns_namespace.name}:${local.backend_port}",
  }

  batch_env_vars = merge(local.base_env_vars, {
    "EXECUTION_CONTEXT"    = "batch"
  })
  

  ecs_env_vars_raw = merge(local.base_env_vars, {
    "EXECUTION_CONTEXT"                   = "ecs"
    "REDIS_HOST"                          = module.elasticache.redis_address
    "REDIS_PORT"                          = module.elasticache.redis_port
    "SQS_QUEUE_URL"                       = module.batch_job_queue.sqs_queue_url
    "MAPPING_BATCH_JOB_NAME"              = "${local.name}-mapping-job"
    "MAPPING_BATCH_JOB_QUEUE"             = module.batch_job_mapping.job_queue_name 
    "MAPPING_BATCH_JOB_DEFINITION"        = module.batch_job_mapping.job_definition_name  
    "SIGN_OFF_BATCH_JOB_NAME"             = "${local.name}-sign-off-job"
    "SIGN_OFF_BATCH_JOB_QUEUE"            = module.batch_job_sign_off.job_queue_name 
    "SIGN_OFF_BATCH_JOB_DEFINITION"       = module.batch_job_sign_off.job_definition_name  
  })

  ecs_env_vars = { for k, v in local.ecs_env_vars_raw : k => tostring(v) }

  additional_policy_arns = {for idx, arn in [aws_iam_policy.ecs_exec_custom_policy.arn] : idx => arn}

  backend_port  = 8000

}



#   load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
#  aws_lb_arn                   = module.load_balancer.alb_arn
#  https_listener_arn           = data.aws_lb_listener.lb_listener_443.arn
#  task_additional_iam_policies = local.additional_policy_arns
#  certificate_arn              = data.terraform_remote_state.universal.outputs.certificate_arn
#  target_group_name_override   =  "caddy-mo-${var.env}-tg"

module "backend" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source            = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source             = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.3.0-ecs"
  name               = "${local.name}-backend"
  image_tag          = var.image_tag
  ecr_repository_uri = var.ecr_repository_uri
  ecs_cluster_id     = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  ecs_cluster_name   = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  https_listener_arn = module.frontend.https_listener_arn
  memory             = local.ecs_memory
  cpu                = local.ecs_cpus
  health_check = {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    accepted_response   = "200"
    path                = "/"
    timeout             = 6
    port                = local.backend_port
  }
  environment_variables = local.ecs_env_vars

  target_group_name_override = "consult-backend-${var.env}-tg"


  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  container_port               = "8000"
  load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                   = module.load_balancer.alb_arn
  host                         = local.host_backend
  # create_listener              = true
  task_additional_iam_policies = local.additional_policy_arns
  additional_execution_role_tags = {
    "RolePassableByRunner" = "True"
  }
  entrypoint = ["./start.sh"]
  certificate_arn = data.terraform_remote_state.universal.outputs.certificate_arn

  service_discovery_service_arn = aws_service_discovery_service.service_discovery_service.arn
  create_networking = false
  create_listener   = false

  additional_security_group_ingress = [
    {
      purpose          = "Frontend to backend container port"
      port             = local.backend_port
      additional_sg_id = module.frontend.ecs_sg_id
    }
  ]

  depends_on = [module.frontend]
}

module "frontend" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source            = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source             = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.3.0-ecs"
  name               = "${local.name}-frontend"
  image_tag          = var.image_tag
  ecr_repository_uri = var.frontend_repository_uri
  ecs_cluster_id     = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  ecs_cluster_name   = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  memory             = local.ecs_memory
  cpu                = local.ecs_cpus
  health_check = {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    accepted_response   = "200"
    path                = "/health"
    timeout             = 6
    port                = 3000
  }
  environment_variables = local.ecs_env_vars

  target_group_name_override = "consult-frontend-${var.env}-tg"


  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  container_port               = "3000"
  load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                   = module.load_balancer.alb_arn
  host                         = local.host
  create_listener              = true
  task_additional_iam_policies = local.additional_policy_arns
  certificate_arn = data.terraform_remote_state.universal.outputs.certificate_arn
}

module "worker" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source            = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source             = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.3.0-ecs"
  name               = "${local.name}-worker"
  image_tag          = var.image_tag
  ecr_repository_uri = var.ecr_repository_uri
  ecs_cluster_id     = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  ecs_cluster_name   = data.terraform_remote_state.platform.outputs.ecs_cluster_name
  certificate_arn    = data.terraform_remote_state.universal.outputs.certificate_arn
  memory             = local.ecs_memory
  cpu                = local.ecs_cpus
  health_check = {
    healthy_threshold   = 3
    unhealthy_threshold = 3
    accepted_response   = "200"
    path                = "/"
    timeout             = 6
    port                = 8000
  }
  environment_variables = local.ecs_env_vars

  autoscaling_maximum_target = 4

  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  container_port               = "8000"
  load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                   = module.load_balancer.alb_arn
  host                         = local.host
  create_listener              = false
  create_networking            = false
  task_additional_iam_policies = local.additional_policy_arns
  additional_execution_role_tags = {
    "RolePassableByRunner" = "True"
  }
  entrypoint = ["./start-worker.sh"]
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
