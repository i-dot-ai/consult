variable "image_tag" {
  description = "The tag of the image to use"
  type        = string
  default     = "latest"
}

variable "region" {
  type        = string
  description = "AWS region for infrastructure to be deployed to"
  default = "eu-west-2"
}

variable "state_bucket" {
  type        = string
  description = "Name of the S3 bucket to use a terraform state"
}

variable "domain_name" {
  type        = string
  description = "The base domain name for the project"
}

variable "env" {
  type        = string
  description = "environment"
  default     = "dev"
}

variable "project_name" {
  type        = string
  description = "Name of project"
}

variable "team_name" {
  type        = string
  description = "The name of the team"
}

variable "universal_tags" {
  type        = map(string)
  description = "Map to tag resources with"
}

variable "github_org" {
  type        = string
  default     = "github.com/i-dot-ai/"
  description = "The default I.AI GitHub Org URL"
}

variable "repository_name" {
  type        = string
  description = "The GitHub repository name"
}

variable "deployed_via" {
  type        = string
  default     = "GitHub_Actions"
  description = "Mechanism for how the Infra was deployed."
}

variable "security_level" {
  type        = string
  default     = "base"
  description = "Security Level of the infrastructure."
}

variable "scope" {
  description = "Scope of the WAF, either 'CLOUDFRONT' or 'REGIONAL'"
  type        = string
  default     = "REGIONAL"
}

# <old-variables>

variable "developer_ips" {
  type        = list(string)
  description = "List of developer IPs"
}

variable "external_ips" {
  type        = list(string)
  description = "List of external IPs"
}

variable "internal_ips" {
  type        = list(string)
  description = "IP's of No10 and CO"
}

# </old-variables>

