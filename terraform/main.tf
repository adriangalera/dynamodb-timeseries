provider "aws" {
  region = "eu-west-1"
}

variable "app-prefix" {
  type = string
  default = "test_ocado"
}

data "aws_caller_identity" "current" { }
data "aws_region" "current" {}

terraform {
  backend "s3" {
    encrypt        = true
    bucket         = "gal-terraform-state"
    key            = "dynamodb-timeseries"
    region         = "eu-west-1"
  }
}