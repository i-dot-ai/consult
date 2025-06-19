locals {
  batch_image_ecr_url = var.ecr_repository_uri
}

module "batch_compute" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source          = "../../i-ai-core-infrastructure/modules/batch/batch_compute_environment"
  source                  = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/batch-compute-environment?ref=v4.0.0-batch-compute-environment"
  account_id              = var.account_id
  name                    = local.name
  region                  = var.region
  vpc_id                  = data.terraform_remote_state.vpc.outputs.vpc_id
  desired_vcpus           = 8
  min_vcpus               = 0
  max_vcpus               = 20
  private_subnets         = data.terraform_remote_state.vpc.outputs.private_subnets
  instance_type           = "g5.xlarge"
  additional_iam_policies = { "batch" : aws_iam_policy.batch.arn }
  permissions_boundary_name = "infra/${local.name}-perms-boundary-app"
}

module "batch_job_definition" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source                  = "../../i-ai-core-infrastructure/modules/batch/batch_job_definitons"
  source                   = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/batch-job-definitions?ref=v4.0.0-batch-job-definitions"
  name                     = local.name
  compute_environment_arn  = [module.batch_compute.ec2_compute_environment_arn]
  image                    = "${local.batch_image_ecr_url}:${var.image_tag}"
  use_fargate              = false
  env_vars                 = local.batch_env_vars
  additional_iam_policies  = { "batch" : aws_iam_policy.batch.arn }
  task_memory_requirements = local.batch_memory
  task_vcpu_requirements   = local.batch_vcpus
  iam_role_name            = "${local.name}-batch-job-role"
  permissions_boundary_name = "infra/${local.name}-perms-boundary-app"
}


resource "aws_iam_policy" "batch" {
  name        = "${local.name}-batch-additional-policy"
  description = "Additional permissions for consultations Batch task"
  policy      = data.aws_iam_policy_document.batch.json
  tags = {
    Environment = terraform.workspace
    Deployed    = "github"
  }
}

data "aws_iam_policy_document" "batch" {
  # checkov:skip=CKV_AWS_109:KMS policies can't be restricted
  # checkov:skip=CKV_AWS_111:KMS policies can't be restricted
  # checkov:skip=CKV_AWS_356:Allow for policies to not have resource limits

  statement {
    effect = "Allow"
    actions = [
      "bedrock:Invoke*",
      "bedrock:Get*",
      "bedrock:List*"
    ]
    resources = [
      "*"
    ]
  }
}
