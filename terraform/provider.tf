terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=4.2.0"
    }
  }

  required_version = ">= 1.2.2"

  backend "s3" {
    key = "consultation-analyser/terraform.tfstate"
  }

}

provider "aws" {
  default_tags {
    tags = {
      "platform:repository" : "${var.github_org}${var.repository_name}",
      "platform:environment" : terraform.workspace,
      "platform:deployed-via" : var.deployed_via,
      "platform:security-level" : var.security_level # https://docs.google.com/document/d/160uNmza2JFUsBb9C0mRZnCN7LM-rWltWA0os5ECWLm8/edit#heading=h.7sil3migh1p2

      Organisation  = "co"
      Department    = "i-dot-ai"
      "Cost Centre" = "i-dot-ai"
      BillingProject = var.repository_name
    }
  }
}
