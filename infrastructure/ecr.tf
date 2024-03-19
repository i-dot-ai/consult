module "ecr_front_end" {
  source = "../../i-ai-core-infrastructure//modules/ecr"

  project_name_prefix = var.project_name
  container_name      = "front-end"
}

module "ecr_pre_processing" {
  source              = "../../i-ai-core-infrastructure//modules/ecr"

  project_name_prefix = var.project_name
  container_name      = "pre-processing"
}

module "ecr" {
  source                = "../../i-ai-core-infrastructure//modules/ecr"
  project_name          = var.project_name
  container_name_suffix = null
}
