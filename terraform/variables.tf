variable "backend_sentry_dsn" {
  type        = string
  description = "The sentry DSN for the backend application"
}

variable "deployed_via" {
  type        = string
  default     = "GitHub_Actions"
  description = "Mechanism for how the Infra was deployed."
}

variable "domain_name" {
  type        = string
  description = "The base domain name for the project"
}

variable "edge_networking_enabled" {
  type        = bool
  description = "Whether to enable edge networking configuration."
}

variable "env" {
  type        = string
  description = "environment"
  default     = "dev"
}

variable "frontend_sentry_dsn" {
  type        = string
  description = "The sentry DSN for the backend application"
}

variable "github_org" {
  type        = string
  default     = "github.com/i-dot-ai/"
  description = "The default I.AI GitHub Org URL"
}

variable "image_tag" {
  description = "The tag of the image to use"
  type        = string
  default     = "latest"
}

variable "project_name" {
  type        = string
  description = "Name of project"
}

variable "repository_name" {
  type        = string
  description = "The GitHub repository name"
}

variable "scope" {
  description = "Scope of the WAF, either 'CLOUDFRONT' or 'REGIONAL'"
  type        = string
  default     = "REGIONAL"
}

variable "security_level" {
  type        = string
  default     = "base"
  description = "Security Level of the infrastructure."
}

variable "state_bucket" {
  type        = string
  description = "Name of the S3 bucket to use a terraform state"
}

variable "team_name" {
  type        = string
  description = "The name of the team"
}

variable "universal_tags" {
  type        = map(string)
  description = "Map to tag resources with"
}
