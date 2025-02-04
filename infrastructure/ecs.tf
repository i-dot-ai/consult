locals {
  rds_fqdn        = "postgres://${module.rds.rds_instance_username}:${module.rds.rds_instance_db_password}@${module.rds.db_instance_address}/${module.rds.db_instance_name}"
  secret_env_vars = jsondecode(data.aws_secretsmanager_secret_version.env_vars.secret_string)
  base_env_vars = {
    "ENVIRONMENT"                          = terraform.workspace,
    "DJANGO_SECRET_KEY"                    = data.aws_secretsmanager_secret_version.django_secret.secret_string,
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
    "AWS_BUCKET_NAME"                      = "${var.team_name}-${terraform.workspace}-consult-ai-data",
  }

  batch_env_vars = merge(local.base_env_vars, {
    "EXECUTION_CONTEXT"    = "batch"
  })

  ecs_env_vars = merge(local.base_env_vars, {
    "BATCH_JOB_QUEUE"      = module.batch_job_definition.job_queue_name,
    "BATCH_JOB_DEFINITION" = module.batch_job_definition.job_definition_name,
    "EXECUTION_CONTEXT"    = "ecs"
    "REDIS_HOST"           = module.elasticache.redis_address,
    "REDIS_PORT"           = module.elasticache.redis_port,
  })

  additional_policy_arns = {for idx, arn in [aws_iam_policy.ecs.arn] : idx => arn}
}

module "ecs" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source            = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source             = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.0.0-ecs"
  name               = local.name
  image_tag          = var.image_tag
  ecr_repository_uri = var.ecr_repository_uri
  ecs_cluster_id     = data.terraform_remote_state.platform.outputs.ecs_cluster_id
  ecs_cluster_name   = data.terraform_remote_state.platform.outputs.ecs_cluster_name
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

  vpc_id                       = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets              = data.terraform_remote_state.vpc.outputs.private_subnets
  container_port               = "8000"
  load_balancer_security_group = module.load_balancer.load_balancer_security_group_id
  aws_lb_arn                   = module.load_balancer.alb_arn
  host                         = local.host
  create_listener              = true
  task_additional_iam_policies = local.additional_policy_arns
  additional_execution_role_tags = {
    "RolePassableByRunner" = "True"
  }
  entrypoint = ["./start.sh"]
  certificate_arn = data.terraform_remote_state.universal.outputs.certificate_arn
}

module "worker" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  #source            = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/ecs" # For testing local changes
  source             = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecs?ref=v5.0.0-ecs"
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


resource "aws_iam_policy" "ecs" {
  name        = "${local.name}-ecs-additional-policy"
  description = "Additional permissions for consultations ECS task"
  policy      = data.aws_iam_policy_document.ecs.json
  tags = {
    Environment = terraform.workspace
    Deployed    = "github"
  }
}

data "aws_iam_policy_document" "ecs" {
  # checkov:skip=CKV_AWS_109:KMS policies can't be restricted
  # checkov:skip=CKV_AWS_111:KMS policies can't be restricted

  statement {
    effect = "Allow"
    actions = [
      "batch:DescribeJobQueues",
      "batch:SubmitJob",
      "kms:GenerateDataKey",
      "kms:Decrypt",
    ]
    resources = [
      "*",
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:List*",
      "s3:Get*",
      "s3:GetObject",
      "s3:PutObject*"
    ]
    resources = [
      "arn:aws:s3:::${local.name}-data/app_data/*"
    ]
  }
}
