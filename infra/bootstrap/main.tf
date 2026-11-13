provider "aws" {
  region              = var.aws_region
  profile             = var.aws_profile
  allowed_account_ids = [var.target_account_id]

  default_tags {
    tags = {
      Environment = "learning"
      ManagedBy   = "Terraform"
      Project     = "SupportDesk"
    }
  }
}

locals {
  github_oidc_provider_arn = var.create_github_oidc_provider ? (
    aws_iam_openid_connect_provider.github[0].arn
  ) : var.github_oidc_provider_arn
  github_repository_subject = "repo:${var.github_owner}/${var.github_repository}"
  platform_state_key        = "learning/platform.tfstate"
  state_bucket_name         = "support-desk-terraform-state-${var.target_account_id}"
}

resource "aws_s3_bucket" "terraform_state" {
  bucket        = local.state_bucket_name
  force_destroy = false
}

resource "aws_s3_bucket_ownership_controls" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    blocked_encryption_types = ["SSE-C"]
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.terraform_state]
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "github_plan" {
  name                 = "support-desk-github-plan"
  description          = "Plans Support Desk infrastructure from trusted GitHub workflows."
  max_session_duration = 3600

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TrustProtectedPlanEnvironment"
        Effect = "Allow"
        Principal = {
          Federated = local.github_oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "${local.github_repository_subject}:environment:${var.github_plan_environment}"
          }
        }
      },
    ]
  })
}

resource "aws_iam_role" "github_apply" {
  name                 = "support-desk-github-apply"
  description          = "Applies Support Desk infrastructure from the protected GitHub environment."
  max_session_duration = 3600

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TrustProtectedEnvironment"
        Effect = "Allow"
        Principal = {
          Federated = local.github_oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "${local.github_repository_subject}:environment:${var.github_environment}"
          }
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "github_plan_state" {
  name   = "support-desk-terraform-state-plan"
  role   = aws_iam_role.github_plan.id
  policy = local.plan_state_policy
}

resource "aws_iam_role_policy" "github_apply_state" {
  name   = "support-desk-terraform-state-apply"
  role   = aws_iam_role.github_apply.id
  policy = local.apply_state_policy
}

resource "aws_iam_role_policy" "github_plan_platform" {
  name   = "support-desk-platform-plan"
  role   = aws_iam_role.github_plan.id
  policy = local.plan_platform_policy
}

resource "aws_iam_role_policy" "github_apply_platform" {
  name   = "support-desk-platform-apply"
  role   = aws_iam_role.github_apply.id
  policy = local.apply_platform_policy
}
