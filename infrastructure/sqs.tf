module "batch_job_queue" {
  # source        = "../../i-dot-ai-core-terraform-modules//modules/infrastructure/sqs" # For testing local changes
  source         = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/sqs?ref=v1.0.2-sqs"
  name           = "${local.name}-batch-job-queue"
  kms_key        = data.terraform_remote_state.platform.outputs.kms_key_arn
  universal_tags = var.universal_tags
}

