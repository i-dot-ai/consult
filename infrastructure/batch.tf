locals {
  batch_image_ecr_url = var.ecr_repository_uri
}

module "batch_compute" {
  source          = "../../i-ai-core-infrastructure/modules/batch/batch_compute_environment"
  account_id      = var.account_id
  name            = local.name
  region          = var.region
  vpc_id          = data.terraform_remote_state.vpc.outputs.vpc_id
  desired_vcpus   = 0
  min_vcpus       = 0
  max_vcpus       = 20
  private_subnets = data.terraform_remote_state.vpc.outputs.private_subnets
  state_bucket    = var.state_bucket
  instance_type   = "g5.xlarge"
  additional_iam_policy   = aws_iam_policy.batch.arn
}

module "batch_job_definition" {
  source                  = "../../i-ai-core-infrastructure/modules/batch/batch_job_definitons"
  name                    = local.name
  compute_environment_arn = [module.batch_compute.ec2_compute_environment_arn]
  state_bucket            = var.state_bucket
  image                   = "${local.batch_image_ecr_url}:${var.image_tag}"
  fargate_flag            = false
  env_vars                = local.batch_env_vars
  additional_iam_policy   = aws_iam_policy.batch.arn
  task_memory_requirements = local.batch_memory
  task_vcpu_requirements   = local.batch_vcpus
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

  statement {
    effect = "Allow"
    actions = [
      "sagemaker:CreateEndpoint",
      "sagemaker:InvokeEndpoint",
      "sagemaker:DescribeEndpoint"
    ]
    resources = [
      "*"
    ]
  }
}
