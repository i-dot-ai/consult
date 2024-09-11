locals {
  container_name_suffix = null
  ecr_name              = local.container_name_suffix != null ? "${var.project_name}-${local.container_name_suffix}" : var.project_name
}

module "ecr" {
  # checkov:skip=CKV_TF_1: We're using semantic versions instead of commit hash
  # source = "../../../i-ai-core-infrastructure//modules/ecr"
  source = "git::https://github.com/i-dot-ai/i-dot-ai-core-terraform-modules.git//modules/infrastructure/ecr?ref=v1.0.0-ecr"
  name   = var.project_name
}
