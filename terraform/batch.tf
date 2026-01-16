locals {
  batch_mapping_image_url = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.id}.amazonaws.com/consult-pipeline-mapping:${var.image_tag}"
  batch_sign_off_image_url = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.id}.amazonaws.com/consult-pipeline-sign-off:${var.image_tag}"
  
  llm_gateway_url        = "https://llm-gateway.i.ai.gov.uk/"
}

module "batch_compute" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source          = "../../i-ai-core-infrastructure/modules/batch/batch_compute_environment"
  source                  = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/batch-compute-environment?ref=v4.0.0-batch-compute-environment"
  account_id              = data.aws_caller_identity.current.id
  name                    = local.name
  region                  = data.aws_region.current.id
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets         = data.terraform_remote_state.vpc.outputs.private_subnets
  additional_iam_policies = { "batch" : aws_iam_policy.ecs_exec_custom_policy.arn }
  use_fargate             = true
  desired_vcpus           = 2
  min_vcpus               = 2
  max_vcpus               = 4
}

module "batch_job_mapping" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                  = "../../i-ai-core-infrastructure/modules/batch/batch_job_definitons"
  source                   = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/batch-job-definitions?ref=v4.0.1-batch-job-definitions"
  name                     = "${local.name}-mapping"
  image                    = local.batch_mapping_image_url
  compute_environment_arn  = [module.batch_compute.fargate_compute_environment_arn]
  use_fargate              = true
  iam_role_name            = "${local.name}-mapping-role"
  platform_capabilities    = ["FARGATE"]
  task_memory_requirements = "2048"
  env_vars                 = merge(local.base_env_vars, {
    "EXECUTION_CONTEXT"        = "batch"
    "DOCKER_BUILDER_CONTAINER" = "${var.project_name}-mapping"
    "APP_NAME"                 = "${var.project_name}-mapping"
  })
  additional_iam_policies  = { "batch" : aws_iam_policy.ecs_exec_custom_policy.arn }
  secrets = [
    for k, v in aws_ssm_parameter.env_secrets : {
      name = regex("([^/]+$)", v.arn)[0], 
      valueFrom = v.arn
    }
  ]
}

module "batch_job_sign_off" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                  = "../../i-ai-core-infrastructure/modules/batch/batch_job_definitons"
  source                   = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/batch-job-definitions?ref=v4.0.1-batch-job-definitions"
  name                     = "${local.name}-sign-off"
  image                    = local.batch_sign_off_image_url
  compute_environment_arn  = [module.batch_compute.fargate_compute_environment_arn]
  use_fargate              = true
  iam_role_name            = "${local.name}-sign-off-role"
  platform_capabilities    = ["FARGATE"]
  task_memory_requirements = "2048"
  env_vars                 = merge(local.base_env_vars, {
    "EXECUTION_CONTEXT"        = "batch"
    "APP_NAME"                 = "${var.project_name}-sign-off"
    "DOCKER_BUILDER_CONTAINER" = "consult-sign-off",
  })
  additional_iam_policies  = { "batch" : aws_iam_policy.ecs_exec_custom_policy.arn }
  secrets = [
    for k, v in aws_ssm_parameter.env_secrets : {
      name = regex("([^/]+$)", v.arn)[0], 
      valueFrom = v.arn
    }
  ]
}

