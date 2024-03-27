locals {
  cloudwatch_log_group = "${var.project_name}-${terraform.workspace}-logs"
}

variable "project_name" {
  type        = string
  description = "Name of project"
}

variable "container_port" {
  type        = number
  description = "The port to run the application on"
  default     = 80
}

variable "cpu" {
  type        = number
  default     = 512
  description = "The cpu resource to give to the task"
}

variable "cognito_usernames" {
  type        = list(string)
  description = "List of usernames to be added"
}

variable "developer_ips" {
  type        = list(string)
  description = "List of developer IPs"
}

variable "domain_name" {
  type        = string
  description = "The base domain name for the project"
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

variable "image_tag" {
  type        = string
  description = "The tag of the image to use"
}

# variable "ecr_repository_uri" {
#   type        = string
#   description = "ECR repo uri"
# }

# variable "cpu" {
#   type        = number
#   default     = 512
#   description = "The cpu resource to give to the task"
# }

# variable "memory" {
#   type        = number
#   description = "The memory resource to give to the task"
#   default     = 1024
# }

variable "container_port" {
  type        = number
  description = "The port to run the application on"
  default     = 80
}

# variable "environment_variables" {
#   type        = map(any)
#   default     = { "ENVIRONMENT" : "dev" }
#   description = "A map of the environment variables to be passed to the ECS task"
# }

# variable "app-replica-count-desired" {
#   type        = number
#   default     = 1
#   description = "The desired number of replicas"
# }

# variable "health_check" {
#   type = object({
#     accepted_response = string
#     path              = string
#     timeout           = number
#   })
#   default = {
#     accepted_response = "200"
#     path              = "/health"
#     timeout           = 5
#   }
#   description = "Set the health check configuration for the target group"
# }

variable "state_bucket" {
  type        = string
  description = "Name of the S3 bucket to use a terraform state"
}

variable "region" {
  type        = string
  description = "aws region"
  default     = "eu-west-2"
}

variable "env" {
  type        = string
  description = "environment"
  default     = "dev"
}


variable "cognito_usernames" {
  type        = list(string)
  description = "List of usernames to be added"
}

variable "domain_name" {
  type        = string
  description = "The base domain name for the project"
}

variable "developer_ips" {
  type        = list(string)
  description = "List of developer IPs"
}

variable "ecr_repository_uri" {
  type        = string
  description = "ECR repo uri"
}

variable "hosted_zone_id" {
  type        = string
  description = "Route 53 Hosted Zone"
}



# variable "prefix" {
#   type        = string
#   description = "value to prefix resources with"
#   default     = "i-dot-ai"
# }

# variable "ecs_cluster_name" {
#   type        = string
#   description = "ECS cluster name to attach service to"
# }
