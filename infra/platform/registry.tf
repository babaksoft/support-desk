resource "aws_ecr_repository" "application" {
  name                 = "support-desk"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "application" {
  repository = aws_ecr_repository.application.name
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Retain the ten newest release images."
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      },
    ]
  })
}

resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "support-desk/learning/openai-api-key"
  description             = "OpenAI API key for the temporary Support Desk learning deployment."
  recovery_window_in_days = 7
}

resource "random_password" "streamlit_cookie" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "streamlit_auth" {
  name                    = "support-desk/learning/streamlit-auth"
  description             = "Cognito client and cookie secrets for the temporary operator interface."
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "streamlit_auth" {
  secret_id = aws_secretsmanager_secret.streamlit_auth.id
  secret_string = jsonencode({
    client_secret = aws_cognito_user_pool_client.operators.client_secret
    cookie_secret = random_password.streamlit_cookie.result
  })
}

