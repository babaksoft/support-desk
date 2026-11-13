output "cloudfront_url" {
  description = "Public HTTPS entry point for the temporary learning deployment."
  value       = local.cloudfront_url
}

output "cognito_callback_url" {
  description = "Exact Streamlit OIDC callback registered with Cognito."
  value       = local.cognito_callback_url
}

output "cognito_google_callback_url" {
  description = "Callback URL to register in the Google OAuth client."
  value       = "https://${aws_cognito_user_pool_domain.operators.domain}.auth.${var.aws_region}.amazoncognito.com/oauth2/idpresponse"
}

output "cognito_issuer" {
  description = "Issuer used by the API to validate Cognito access tokens."
  value       = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.operators.id}"
}

output "cognito_user_pool_client_id" {
  description = "Confidential app-client identifier used by the operator UI."
  value       = aws_cognito_user_pool_client.operators.id
}

output "cognito_user_pool_id" {
  description = "User pool that owns operator identities and group membership."
  value       = aws_cognito_user_pool.operators.id
}

output "ecr_repository_url" {
  description = "Repository destination for immutable application images."
  value       = aws_ecr_repository.application.repository_url
}

output "ecs_cluster_name" {
  description = "Cluster used by deployment, smoke, rollback, and teardown operations."
  value       = aws_ecs_cluster.application.name
}

output "ecs_service_name" {
  description = "Service used by deployment, smoke, rollback, and teardown operations."
  value       = aws_ecs_service.application.name
}

output "openai_secret_arn" {
  description = "Secret destination that must receive the API key outside Terraform state."
  value       = aws_secretsmanager_secret.openai_api_key.arn
}

output "streamlit_auth_secret_arn" {
  description = "Secret containing the generated confidential Streamlit OIDC settings."
  value       = aws_secretsmanager_secret.streamlit_auth.arn
}

output "postgresql_subnet_group_name" {
  description = "Reserved private subnet group for the later PostgreSQL slice."
  value       = aws_db_subnet_group.future_postgresql.name
}

