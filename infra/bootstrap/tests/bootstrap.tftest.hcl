mock_provider "aws" {}

run "creates_bounded_bootstrap_resources" {
  command = plan

  variables {
    target_account_id = "123456789012"
  }

  assert {
    condition     = aws_s3_bucket.terraform_state.bucket == "support-desk-terraform-state-123456789012"
    error_message = "The state bucket name must be scoped to the target account."
  }

  assert {
    condition     = aws_s3_bucket.terraform_state.force_destroy == false
    error_message = "The state bucket must reject recursive deletion."
  }

  assert {
    condition     = aws_s3_bucket_versioning.terraform_state.versioning_configuration[0].status == "Enabled"
    error_message = "The state bucket must preserve version history."
  }

  assert {
    condition     = aws_s3_bucket_public_access_block.terraform_state.restrict_public_buckets
    error_message = "The state bucket must block public access."
  }

  assert {
    condition = one(
      one(aws_s3_bucket_server_side_encryption_configuration.terraform_state.rule).apply_server_side_encryption_by_default
    ).sse_algorithm == "AES256"
    error_message = "The state bucket must encrypt objects with SSE-S3."
  }

  assert {
    condition     = aws_iam_role.github_plan.name == "support-desk-github-plan"
    error_message = "The GitHub plan role must use the bounded project name."
  }

  assert {
    condition     = aws_iam_role.github_apply.name == "support-desk-github-apply"
    error_message = "The GitHub apply role must use the bounded project name."
  }
}

run "accepts_an_existing_github_provider" {
  command = plan

  variables {
    target_account_id           = "123456789012"
    create_github_oidc_provider = false
    github_oidc_provider_arn    = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
  }

  assert {
    condition     = length(aws_iam_openid_connect_provider.github) == 0
    error_message = "Bootstrap must not duplicate an existing account-level provider."
  }
}
