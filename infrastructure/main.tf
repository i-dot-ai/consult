terraform {
  backend "s3" {
    key = "consultation-analyser/terraform.tfstate"
  }
}

provider "random" {

}
