
module "ecr_front_end" {
  source = "../../i-ai-core-infrastructure//modules/ecr"

  project_name_prefix = var.project_name
  container_name      = "front-end"
}

module "ecr_back_end" {
  source              = "../../i-ai-core-infrastructure//modules/ecr"
  project_name_prefix = var.project_name
  container_name      = "pre-processing"
}
