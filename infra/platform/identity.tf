resource "aws_cognito_user_pool" "operators" {
  name                     = "${local.name}-operators"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  deletion_protection      = "INACTIVE"
  mfa_configuration        = "OFF"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
  }
}

resource "aws_cognito_user_group" "operators" {
  name         = local.operator_group
  description  = "Operators allowed to use Support Desk application actions."
  user_pool_id = aws_cognito_user_pool.operators.id
}

resource "aws_cognito_user_pool_domain" "operators" {
  domain       = local.cognito_domain_prefix
  user_pool_id = aws_cognito_user_pool.operators.id
}

resource "aws_cognito_user_pool_client" "operators" {
  name         = "support-desk-streamlit"
  user_pool_id = aws_cognito_user_pool.operators.id

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["email", "openid"]
  callback_urls                        = [local.cognito_callback_url]
  logout_urls                          = [local.cognito_logout_url]
  generate_secret                      = true
  prevent_user_existence_errors        = "ENABLED"
  supported_identity_providers         = ["Google"]

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 1

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

