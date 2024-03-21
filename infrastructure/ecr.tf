
module "ecr" {
  source = "../../i-ai-core-infrastructure//modules/ecr"

  project_name_prefix = var.project_name
  container_name      = "front-end"
}
