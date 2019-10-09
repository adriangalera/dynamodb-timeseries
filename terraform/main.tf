provider "aws" {
  profile = "gal"
  region = "eu-west-1"
}

variable "app-prefix" {
  type = string
  default = "test_ocado"
}

data "aws_caller_identity" "current" { }
data "aws_region" "current" {}

