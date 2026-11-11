locals {
  state_bucket_arn = aws_s3_bucket.terraform_state.arn
  state_object_arn = "${local.state_bucket_arn}/${local.platform_state_key}"
  lock_object_arn  = "${local.state_object_arn}.tflock"

  plan_state_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListStatePath"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [local.state_bucket_arn]
        Condition = {
          StringEquals = {
            "s3:prefix" = [
              local.platform_state_key,
              "${local.platform_state_key}.tflock",
            ]
          }
        }
      },
      {
        Sid      = "ReadState"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = [local.state_object_arn, local.lock_object_arn]
      },
      {
        Sid      = "ManageStateLock"
        Effect   = "Allow"
        Action   = ["s3:DeleteObject", "s3:PutObject"]
        Resource = [local.lock_object_arn]
      },
    ]
  })

  apply_state_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListStatePath"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [local.state_bucket_arn]
        Condition = {
          StringEquals = {
            "s3:prefix" = [
              local.platform_state_key,
              "${local.platform_state_key}.tflock",
            ]
          }
        }
      },
      {
        Sid      = "UpdateState"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = [local.state_object_arn]
      },
      {
        Sid      = "ManageStateLock"
        Effect   = "Allow"
        Action   = ["s3:DeleteObject", "s3:GetObject", "s3:PutObject"]
        Resource = [local.lock_object_arn]
      },
    ]
  })
}
