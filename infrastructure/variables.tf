variable "account_id" {
  type        = string
  description = "AWS Account ID"
}

variable "app-replica-count-desired" {
  type        = number
  default     = 1
  description = "The desired number of replicas"
}

variable "container_port" {
  type        = number
  description = "The port to run the application on"
  default     = 80
}

variable "cpu" {
  type        = number
  default     = 1024
  description = "The cpu resource to give to the task"
}

variable "vcpus" {
  type        = number
  description = "The number of vcpus to give to the task."
  default     = 2
}

variable "developer_ips" {
  type        = list(string)
  description = "List of developer IPs"
}

variable "domain_name" {
  type        = string
  description = "The base domain name for the project"
}

variable "external_ips" {
  type        = list(string)
  description = "List of external IPs"
}

variable "ecr_repository_uri" {
  type        = string
  description = "ECR repo uri"
}

variable "ecs_cluster_name" {
  type        = string
  description = "ECS cluster name to attach service to"
  default     = "null"
}

variable "environment_variables" {
  type        = map(any)
  default     = { "ENVIRONMENT" : "dev" }
  description = "A map of the environment variables to be passed to the ECS task"
}

variable "env" {
  type        = string
  description = "environment"
  default     = "dev"
}

variable "health_check" {
  type = object({
    accepted_response = string
    path              = string
    timeout           = number
  })
  default = {
    accepted_response = "200"
    path              = "/health"
    timeout           = 5
  }
  description = "Set the health check configuration for the target group"
}

variable "hosted_zone_id" {
  type        = string
  description = "Route 53 Hosted Zone"
}

variable "internal_ips" {
  type        = list(string)
  description = "IP's of No10 and CO"
}

variable "image_tag" {
  type        = string
  description = "The tag of the image to use"
}

variable "memory" {
  type        = number
  description = "The memory resource to give to the task"
  default     = 2048
}

variable "ecs_memory" {
  type        = number
  description = "The memory resource to give to the ecs"
  default     = 2048
}

variable "ecs_cpus" {
  type        = number
  description = "The cpu resource to give to the task"
  default     = 1
}

variable "prefix" {
  type        = string
  description = "value to prefix resources with"
  default     = "i-dot-ai"
}

variable "project_name" {
  type        = string
  description = "Name of project"
}

variable "region" {
  type        = string
  description = "aws region"
  default     = "eu-west-2"
}

variable "state_bucket" {
  type        = string
  description = "Name of the S3 bucket to use a terraform state"
}

variable "scope" {
  description = "Scope of the WAF, either 'CLOUDFRONT' or 'REGIONAL'"
  type        = string
  default     = "REGIONAL"
}

variable "team_name" {
  type        = string
  description = "The name of the team"
}

variable "universal_tags" {
  type        = map(string)
  description = "Map to tag resources with"
}

variable "publicly_accessible" {
  type        = bool
  description = "Flag to determine if the database is publicly accessible"
}
