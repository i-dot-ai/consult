locals {
  name = "${var.team_name}-${terraform.workspace}-${var.project_name}"
}
module "postgres" {
  source              = "../../../i-ai-core-infrastructure//modules/postgres"
  kms_secrets_arn     = data.terraform_remote_state.platform.outputs.kms_key_arn
  name                = local.name
  db_name             = "postgres"
  db_instance_address = data.terraform_remote_state.consultations.outputs.db_instance_address
  db_master_username  = data.terraform_remote_state.consultations.outputs.db_instance_address
  db_master_password  = data.terraform_remote_state.consultations.outputs.db_instance_address

}

data "terraform_remote_state" "platform" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "platform/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "consultations" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "consultation-analyser/terraform.tfstate"
    region = var.region
  }
}
