terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket  = "cloud-events-terraform-state"
    key     = "dev/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

locals {
  environment = "dev"
  region      = "us-east-1"
  app_path    = abspath("${path.root}/../../../app")
}

provider "aws" {
  region = local.region
}

module "events" {
  source               = "../../modules/events"
  environment          = local.environment
  aws_region           = local.region
  app_path             = local.app_path
  jwt_secret_name      = "auth/jwt_secret"
  client_secret_prefix = "auth/client/"
}

output "api_base_url" {
  value = module.events.api_base_url
}

output "table_name" {
  value = module.events.table_name
}

output "aws_region" {
  value = local.region
}

output "queue_url" {
  value = module.events.queue_url
}

output "dlq_url" {
  value       = module.events.dlq_url
}