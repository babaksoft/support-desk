mock_provider "aws" {}

override_resource {
  target          = aws_iam_openid_connect_provider.github
  override_during = plan
  values = {
    arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
  }
}

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

  assert {
    condition = (
      jsondecode(aws_iam_role.github_plan.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:sub"] ==
      "repo:babaksoft@15974699/support-desk@1449584851:environment:learning-plan"
    )
    error_message = "The plan role must trust the immutable repository subject and plan environment."
  }

  assert {
    condition = (
      jsondecode(aws_iam_role.github_apply.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:sub"] ==
      "repo:babaksoft@15974699/support-desk@1449584851:environment:learning"
    )
    error_message = "The apply role must trust the immutable repository subject and apply environment."
  }

  assert {
    condition = !contains(
      jsondecode(aws_iam_role_policy.github_plan_platform.policy).Statement[0].Action,
      "ecs:UpdateService",
    )
    error_message = "The plan role must not receive platform mutation permissions."
  }

  assert {
    condition = contains(
      jsondecode(aws_iam_role_policy.github_apply_platform.policy).Statement[0].Action,
      "ecr:PutImage",
    )
    error_message = "The apply role must be able to push immutable release images."
  }

  assert {
    condition = (
      jsondecode(aws_iam_role_policy.github_apply_platform.policy).Statement[1].Resource ==
      "arn:aws:iam::123456789012:role/support-desk-learning-*"
    )
    error_message = "Task-role management must stay scoped to the learning platform."
  }

  assert {
    condition = toset(
      jsondecode(aws_iam_role_policy.github_apply_platform.policy).Statement[2].Condition.StringEquals["iam:AWSServiceName"]
      ) == toset([
      "ecs.amazonaws.com",
      "elasticloadbalancing.amazonaws.com",
      "vpcorigin.cloudfront.amazonaws.com",
    ])
    error_message = "Service-linked role creation must stay limited to required services."
  }

  assert {
    condition     = length(aws_iam_role_policy.github_apply_platform.policy) <= 10240
    error_message = "The apply policy must fit the AWS inline role-policy size limit."
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

run "rejects_invalid_immutable_github_ids" {
  command = plan

  variables {
    target_account_id    = "123456789012"
    github_owner_id      = "owner-id"
    github_repository_id = "0"
  }

  expect_failures = [var.github_owner_id, var.github_repository_id]
}
