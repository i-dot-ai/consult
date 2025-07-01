terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.0.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.6.2"
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
      "platform:environment"    = terraform.workspace
      "platform:deployed-via"   = "github"
      "platform:repository"     = "github.com/i-dot-ai/consult"
      "platform:security-level" = "base"

      Organisation = "co"
      Department = "i-dot-ai"
      "Cost Centre" = "i-dot-ai"
    }
  }
}
