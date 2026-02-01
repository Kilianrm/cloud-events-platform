variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "cloud-event-platform"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "app_path" {
  description = "Path to application source code"
  type        = string
}

