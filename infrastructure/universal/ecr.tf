locals {
  container_name_suffix = null
  ecr_name              = local.container_name_suffix != null ? "${var.project_name}-${local.container_name_suffix}" : var.project_name
}

module "ecr" {
  source = "../../../i-ai-core-infrastructure//modules/ecr"
  name   = var.project_name
}
