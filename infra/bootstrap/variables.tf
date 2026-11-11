variable "target_account_id" {
  description = "AWS account ID that Terraform is allowed to modify."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.target_account_id))
    error_message = "target_account_id must contain exactly 12 digits."
  }
}

variable "aws_profile" {
  description = "Local AWS CLI profile used for bootstrap operations."
  type        = string
  default     = "support-desk-bootstrap"
}

variable "aws_region" {
  description = "AWS region for regional bootstrap resources."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = var.aws_region == "us-east-1"
    error_message = "Slice 1.3 bootstrap resources must remain in us-east-1."
  }
}

variable "github_owner" {
  description = "GitHub organization or user that owns the repository."
  type        = string
  default     = "babaksoft"
}

variable "github_repository" {
  description = "GitHub repository trusted to request AWS credentials."
  type        = string
  default     = "support-desk"
}

variable "github_environment" {
  description = "Protected GitHub environment allowed to apply infrastructure."
  type        = string
  default     = "learning"
}

variable "github_plan_environment" {
  description = "Protected GitHub environment allowed to read state for plans."
  type        = string
  default     = "learning-plan"
}

variable "create_github_oidc_provider" {
  description = "Whether this bootstrap owns the account-level GitHub OIDC provider."
  type        = bool
  default     = true
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub OIDC provider ARN when bootstrap does not create it."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.create_github_oidc_provider ||
      (var.github_oidc_provider_arn != null && can(regex(
        "^arn:aws:iam::[0-9]{12}:oidc-provider/token\\.actions\\.githubusercontent\\.com$",
        var.github_oidc_provider_arn,
      )))
    )
    error_message = "Set a valid GitHub OIDC provider ARN when creation is disabled."
  }
}
