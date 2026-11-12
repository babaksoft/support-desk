provider "aws" {
  region              = var.aws_region
  profile             = var.use_aws_profile ? var.aws_profile : null
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
  name                  = "support-desk-learning"
  cloudfront_origin_id  = "support-desk-streamlit"
  cloudfront_url        = "https://${aws_cloudfront_distribution.application.domain_name}"
  cognito_callback_url  = "${local.cloudfront_url}/"
  cognito_domain_prefix = "support-desk-${var.target_account_id}"
  image_uri             = "${aws_ecr_repository.application.repository_url}@${var.image_digest}"
  operator_group        = "operators"

  subnet_tiers = {
    origin = {
      cidrs  = ["10.32.0.0/24", "10.32.1.0/24"]
      public = false
    }
    application = {
      cidrs  = ["10.32.16.0/24", "10.32.17.0/24"]
      public = true
    }
    database = {
      cidrs  = ["10.32.32.0/24", "10.32.33.0/24"]
      public = false
    }
  }
  subnets = merge([
    for tier_name, tier in local.subnet_tiers : {
      for index, cidr in tier.cidrs : "${tier_name}-${index + 1}" => {
        availability_zone_id = var.availability_zone_ids[index]
        cidr                 = cidr
        public               = tier.public
        tier                 = tier_name
      }
    }
  ]...)
}

