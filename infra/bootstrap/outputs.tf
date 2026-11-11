output "github_apply_role_arn" {
  description = "Role assumed by the protected GitHub apply environment."
  value       = aws_iam_role.github_apply.arn
}

output "github_oidc_provider_arn" {
  description = "Account-level GitHub Actions OIDC provider ARN."
  value       = local.github_oidc_provider_arn
}

output "github_plan_role_arn" {
  description = "Role assumed by trusted GitHub plan workflows."
  value       = aws_iam_role.github_plan.arn
}

output "platform_state_key" {
  description = "S3 object key reserved for the learning platform state."
  value       = local.platform_state_key
}

output "terraform_state_bucket" {
  description = "S3 bucket that stores remote Terraform state."
  value       = aws_s3_bucket.terraform_state.id
}
