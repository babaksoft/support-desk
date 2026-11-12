variable "target_account_id" {
  description = "AWS account ID that Terraform is allowed to modify."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.target_account_id))
    error_message = "target_account_id must contain exactly 12 digits."
  }
}

variable "aws_profile" {
  description = "Local AWS CLI profile used for reviewed platform operations."
  type        = string
  default     = "support-desk-bootstrap"
  nullable    = false
}

variable "use_aws_profile" {
  description = "Whether the provider uses the local CLI profile instead of ambient OIDC credentials."
  type        = bool
  default     = true
  nullable    = false
}

variable "aws_region" {
  description = "AWS region for regional application resources."
  type        = string
  default     = "us-east-1"
  nullable    = false

  validation {
    condition     = var.aws_region == "us-east-1"
    error_message = "Slice 1.3 application resources must remain in us-east-1."
  }
}

variable "availability_zone_ids" {
  description = "Two stable us-east-1 zone IDs supported by CloudFront VPC origins."
  type        = list(string)
  default     = ["use1-az1", "use1-az2"]
  nullable    = false

  validation {
    condition = (
      length(var.availability_zone_ids) == 2 &&
      length(distinct(var.availability_zone_ids)) == 2 &&
      alltrue([
        for zone_id in var.availability_zone_ids :
        can(regex("^use1-az[1-6]$", zone_id)) && zone_id != "use1-az3"
      ])
    )
    error_message = "Set two distinct supported us-east-1 zone IDs; use1-az3 is unsupported."
  }
}

variable "image_digest" {
  description = "Immutable sha256 digest of the application image in the managed ECR repository."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.image_digest))
    error_message = "image_digest must be a lowercase sha256 digest."
  }
}

variable "model" {
  description = "OpenAI Responses model identifier used by the bounded live deployment."
  type        = string
  default     = "gpt-5.4-mini-2026-03-17"
  nullable    = false

  validation {
    condition     = length(trimspace(var.model)) > 0 && length(var.model) <= 128
    error_message = "model must contain between 1 and 128 characters."
  }
}

variable "service_desired_count" {
  description = "Number of application tasks; keep zero until the image and secret are ready."
  type        = number
  default     = 0
  nullable    = false

  validation {
    condition     = contains([0, 1], var.service_desired_count)
    error_message = "The learning deployment supports zero or one task."
  }
}

