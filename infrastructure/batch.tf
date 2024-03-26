

module "batch_compute" {
  source          = "../../i-ai-core-infrastructure/modules/batch/batch_compute_environment/"
  project         = "i-dot-ai"
  name            = "consultations"
  region          = var.region
  vpc_id          = data.terraform_remote_state.vpc.outputs.vpc_id
  desired_vcpus   = 0
  min_vcpus       = 0
  max_vcpus       = 20
  private_subnets = data.terraform_remote_state.vpc.outputs.private_subnets
  state_bucket    = var.state_bucket
  instance_type   = "g5.xlarge"
}

module "batch_job_defintiion" {
  source                  = "../../i-ai-core-infrastructure/modules/batch/batch_job_definitons/"
  project                 = "i-dot-ai"
  name                    = "consultations"
  region                  = var.region
  compute_environment_arn = [module.batch_compute.ec2_compute_environment_arn]
  state_bucket            = var.state_bucket
  image                   = module.ecr.ecr_repository_url
  fargate_flag            = false
}
