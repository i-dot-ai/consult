locals {
  consult_pipeline_job_names = ["mapping"]
  batch_mapping_image_url = "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/consult-pipeline-mapping:${var.image_tag}"
  backend_port = 8080
}

module "batch_compute" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source          = "../../i-ai-core-infrastructure/modules/batch/batch_compute_environment"
  source                  = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/batch-compute-environment?ref=v3.1.1-batch-compute-environment"
  account_id              = data.aws_caller_identity.current.id
  name                    = local.name
  region                  = data.aws_region.current.id
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  private_subnets         = data.terraform_remote_state.vpc.outputs.private_subnets
  additional_iam_policies = { "batch" : aws_iam_policy.ecs_exec_custom_policy.arn }
  use_fargate = true
  desired_vcpus = 2
  min_vcpus = 2
  max_vcpus = 4
}

module "batch_job_mapping" {
  for_each = toset(local.consult_pipeline_job_names)
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                  = "../../i-ai-core-infrastructure/modules/batch/batch_job_definitons"
  source                   = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/batch-job-definitions?ref=dk-add-job-role"
  name                     = "${local.name}-${each.value}"
  image                    = local.batch_mapping_image_url
  compute_environment_arn = [module.batch_compute.fargate_compute_environment_arn]
  use_fargate              = true
  iam_role_name            = "${local.name}-${each.value}-role"
  platform_capabilities = ["FARGATE"]
  task_memory_requirements = "2048"
  env_vars                 = {
    "ENVIRONMENT" : terraform.workspace,
    "APP_NAME" : "${local.name}-${each.value}"
    "PORT" : local.backend_port,
    "REPO" : "consult-pipeline-${each.value}",
    "AWS_ACCOUNT_ID": data.aws_caller_identity.current.id,
    "DOCKER_BUILDER_CONTAINER": "consult-pipeline-${each.value}",
  }
  additional_iam_policies  = { "batch" : aws_iam_policy.ecs_exec_custom_policy.arn }
  secrets = [
    for k, v in aws_ssm_parameter.env_secrets : {
      name = regex("([^/]+$)", v.arn)[0], # Extract right-most string (param name) after the final slash
      valueFrom = v.arn
    }
  ]
}