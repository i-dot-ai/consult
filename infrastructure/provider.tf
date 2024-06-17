terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.53.0"
    }
  }
  required_version = ">= 1.3.5"

  backend "s3" {
    key = "consultation-analyser/terraform.tfstate"
  }

}

provider "random" {

}

provider "aws" {
  default_tags {
    tags = {
      platform:environment    = terraform.workspace
      platform:deployed-via   = "github"
      platform:repository     = "https://github.com/i-dot-ai/consultation-analyser"
      platform:security-level = "base"
    }
  }
}
