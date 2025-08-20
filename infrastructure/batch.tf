locals {
  batch_mapping_image_url = "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/consult-pipeline-mapping:${var.image_tag}"
  batch_sign_off_image_url = "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/consult-pipeline-sign-off:${var.image_tag}"

  llm_gateway_name       = var.env == "dev" || var.env == "preprod" ? "llm-gateway.${var.env}" : "llm-gateway"
  llm_gateway_url        = "https://${local.llm_gateway_name}.i.ai.gov.uk"
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
  env_vars                 = {
    "ENVIRONMENT" : terraform.workspace,
    "APP_NAME" : "${local.name}-mapping"
    "REPO" : "consult",
    "AWS_ACCOUNT_ID": data.aws_caller_identity.current.id,
    "DOCKER_BUILDER_CONTAINER": "consult-mapping",
    "OPENAI_API_KEY": data.aws_ssm_parameter.litellm_api_key.value
    "OPENAI_API_BASE": local.llm_gateway_url
  }
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
  env_vars                 = {
    "ENVIRONMENT" : terraform.workspace,
    "APP_NAME" : "${local.name}-sign-off"
    "REPO" : "consult",
    "AWS_ACCOUNT_ID": data.aws_caller_identity.current.id,
    "DOCKER_BUILDER_CONTAINER": "consult-sign-off",
    "OPENAI_API_KEY": data.aws_ssm_parameter.litellm_api_key.value
    "OPENAI_API_BASE": local.llm_gateway_url
  }
  additional_iam_policies  = { "batch" : aws_iam_policy.ecs_exec_custom_policy.arn }
  secrets = [
    for k, v in aws_ssm_parameter.env_secrets : {
      name = regex("([^/]+$)", v.arn)[0], 
      valueFrom = v.arn
    }
  ]
}

