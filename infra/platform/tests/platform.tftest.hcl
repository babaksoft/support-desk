mock_provider "aws" {}

override_resource {
  target          = aws_ecr_repository.application
  override_during = plan
  values = {
    repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/support-desk"
  }
}

override_resource {
  target          = aws_cloudfront_distribution.application
  override_during = plan
  values = {
    domain_name = "example.cloudfront.net"
  }
}

run "builds_bounded_learning_platform" {
  command = plan

  variables {
    target_account_id = "123456789012"
    image_digest      = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }

  assert {
    condition     = aws_vpc.application.cidr_block == "10.32.0.0/16"
    error_message = "The application VPC must use its bounded learning CIDR."
  }

  assert {
    condition     = length(aws_subnet.application) == 6
    error_message = "Origin, application, and future database tiers need two subnets each."
  }

  assert {
    condition = alltrue([
      for key, subnet in aws_subnet.application :
      subnet.map_public_ip_on_launch == false
    ])
    error_message = "Subnets must not assign public addresses implicitly."
  }

  assert {
    condition     = aws_ecr_repository.application.image_tag_mutability == "IMMUTABLE"
    error_message = "Release tags must not be mutable."
  }

  assert {
    condition     = aws_ecr_repository.application.force_delete == false
    error_message = "Terraform must not recursively delete release images."
  }

  assert {
    condition     = aws_ecs_service.application.desired_count == 0
    error_message = "The service must stay stopped until its image and secret are ready."
  }

  assert {
    condition     = aws_ecs_service.application.network_configuration[0].assign_public_ip
    error_message = "The task needs an explicit public address for outbound access without NAT."
  }

  assert {
    condition     = local.image_uri == "123456789012.dkr.ecr.us-east-1.amazonaws.com/support-desk@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    error_message = "The task image reference must use the exact reviewed ECR digest."
  }

  assert {
    condition     = aws_lb.application.internal
    error_message = "The load balancer must remain internal behind the CloudFront VPC origin."
  }

  assert {
    condition     = aws_cloudfront_cache_policy.dynamic.default_ttl == 0
    error_message = "Authenticated application traffic must not be cached."
  }

  assert {
    condition     = aws_cognito_user_pool.operators.admin_create_user_config[0].allow_admin_create_user_only
    error_message = "Public Cognito sign-up must remain disabled."
  }

  assert {
    condition     = aws_cognito_user_pool_client.operators.callback_urls == toset(["https://example.cloudfront.net/oauth2callback"])
    error_message = "Cognito must return the authorization code to Streamlit's OIDC callback."
  }

  assert {
    condition     = aws_cognito_user_pool_client.operators.generate_secret
    error_message = "The server-side OIDC client must remain confidential."
  }

  assert {
    condition     = aws_cognito_user_pool_client.operators.supported_identity_providers == toset(["Google"])
    error_message = "Google must be the only enabled operator identity provider."
  }

  assert {
    condition     = aws_secretsmanager_secret.openai_api_key.recovery_window_in_days == 7
    error_message = "Secret deletion must retain the configured recovery window."
  }

  assert {
    condition     = aws_secretsmanager_secret.streamlit_auth.recovery_window_in_days == 7
    error_message = "OIDC secrets must retain the configured recovery window."
  }
}

run "rejects_a_running_service_above_one_task" {
  command = plan

  variables {
    target_account_id     = "123456789012"
    image_digest          = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    service_desired_count = 2
  }

  expect_failures = [var.service_desired_count]
}

