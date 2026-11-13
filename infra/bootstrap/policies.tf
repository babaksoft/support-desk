locals {
  state_bucket_arn          = aws_s3_bucket.terraform_state.arn
  state_object_arn          = "${local.state_bucket_arn}/${local.platform_state_key}"
  lock_object_arn           = "${local.state_object_arn}.tflock"
  streamlit_auth_secret_arn = "arn:aws:secretsmanager:${var.aws_region}:${var.target_account_id}:secret:support-desk/learning/streamlit-auth-*"

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

  platform_read_actions = [
    "cloudfront:GetCachePolicy",
    "cloudfront:GetDistribution",
    "cloudfront:GetDistributionConfig",
    "cloudfront:GetOriginRequestPolicy",
    "cloudfront:GetVpcOrigin",
    "cloudfront:ListTagsForResource",
    "cognito-idp:DescribeUserPool",
    "cognito-idp:DescribeUserPoolClient",
    "cognito-idp:DescribeUserPoolDomain",
    "cognito-idp:GetGroup",
    "cognito-idp:GetUserPoolMfaConfig",
    "cognito-idp:ListTagsForResource",
    "ec2:Describe*",
    "ec2:GetManagedPrefixListEntries",
    "ec2:GetSecurityGroupsForVpc",
    "ecr:DescribeImages",
    "ecr:DescribeRepositories",
    "ecr:GetLifecyclePolicy",
    "ecr:ListImages",
    "ecr:ListTagsForResource",
    "ecs:DescribeClusters",
    "ecs:DescribeServiceDeployments",
    "ecs:DescribeServices",
    "ecs:DescribeTaskDefinition",
    "ecs:ListServiceDeployments",
    "ecs:ListTagsForResource",
    "elasticloadbalancing:Describe*",
    "iam:GetRole",
    "iam:GetRolePolicy",
    "iam:ListAttachedRolePolicies",
    "iam:ListInstanceProfilesForRole",
    "iam:ListRolePolicies",
    "iam:ListRoleTags",
    "logs:DescribeLogGroups",
    "logs:ListTagsForResource",
    "rds:DescribeDBSubnetGroups",
    "rds:ListTagsForResource",
    "secretsmanager:DescribeSecret",
    "secretsmanager:GetResourcePolicy",
    "secretsmanager:ListSecretVersionIds",
    "sts:GetCallerIdentity",
  ]

  plan_platform_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadLearningPlatform"
        Effect   = "Allow"
        Action   = local.platform_read_actions
        Resource = "*"
      },
      {
        Sid      = "ReadStreamlitAuthSecretValue"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = local.streamlit_auth_secret_arn
      },
    ]
  })

  apply_platform_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ManageLearningPlatform"
        Effect = "Allow"
        Action = concat(local.platform_read_actions, [
          "cloudfront:CreateCachePolicy",
          "cloudfront:CreateDistribution",
          "cloudfront:CreateOriginRequestPolicy",
          "cloudfront:CreateVpcOrigin",
          "cloudfront:DeleteCachePolicy",
          "cloudfront:DeleteDistribution",
          "cloudfront:DeleteOriginRequestPolicy",
          "cloudfront:DeleteVpcOrigin",
          "cloudfront:TagResource",
          "cloudfront:UntagResource",
          "cloudfront:UpdateCachePolicy",
          "cloudfront:UpdateDistribution",
          "cloudfront:UpdateOriginRequestPolicy",
          "cloudfront:UpdateVpcOrigin",
          "cognito-idp:CreateGroup",
          "cognito-idp:CreateUserPool",
          "cognito-idp:CreateUserPoolClient",
          "cognito-idp:CreateUserPoolDomain",
          "cognito-idp:DeleteGroup",
          "cognito-idp:DeleteUserPool",
          "cognito-idp:DeleteUserPoolClient",
          "cognito-idp:DeleteUserPoolDomain",
          "cognito-idp:TagResource",
          "cognito-idp:UntagResource",
          "cognito-idp:UpdateGroup",
          "cognito-idp:UpdateUserPool",
          "cognito-idp:UpdateUserPoolClient",
          "ec2:AssociateRouteTable",
          "ec2:AttachInternetGateway",
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:CreateInternetGateway",
          "ec2:CreateRoute",
          "ec2:CreateRouteTable",
          "ec2:CreateSecurityGroup",
          "ec2:CreateSubnet",
          "ec2:CreateTags",
          "ec2:CreateVpc",
          "ec2:DeleteInternetGateway",
          "ec2:DeleteRoute",
          "ec2:DeleteRouteTable",
          "ec2:DeleteSecurityGroup",
          "ec2:DeleteSubnet",
          "ec2:DeleteTags",
          "ec2:DeleteVpc",
          "ec2:DetachInternetGateway",
          "ec2:DisassociateRouteTable",
          "ec2:ModifySubnetAttribute",
          "ec2:ModifyVpcAttribute",
          "ec2:RevokeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress",
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchDeleteImage",
          "ecr:CompleteLayerUpload",
          "ecr:CreateRepository",
          "ecr:DeleteLifecyclePolicy",
          "ecr:DeleteRepository",
          "ecr:GetAuthorizationToken",
          "ecr:GetDownloadUrlForLayer",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:PutImageScanningConfiguration",
          "ecr:PutImageTagMutability",
          "ecr:PutLifecyclePolicy",
          "ecr:TagResource",
          "ecr:UntagResource",
          "ecr:UploadLayerPart",
          "ecs:CreateCluster",
          "ecs:CreateService",
          "ecs:DeleteCluster",
          "ecs:DeleteService",
          "ecs:DeregisterTaskDefinition",
          "ecs:PutClusterCapacityProviders",
          "ecs:RegisterTaskDefinition",
          "ecs:TagResource",
          "ecs:UntagResource",
          "ecs:UpdateCluster",
          "ecs:UpdateService",
          "elasticloadbalancing:AddTags",
          "elasticloadbalancing:CreateListener",
          "elasticloadbalancing:CreateLoadBalancer",
          "elasticloadbalancing:CreateTargetGroup",
          "elasticloadbalancing:DeleteListener",
          "elasticloadbalancing:DeleteLoadBalancer",
          "elasticloadbalancing:DeleteTargetGroup",
          "elasticloadbalancing:ModifyLoadBalancerAttributes",
          "elasticloadbalancing:ModifyTargetGroup",
          "elasticloadbalancing:ModifyTargetGroupAttributes",
          "elasticloadbalancing:RemoveTags",
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:PutRetentionPolicy",
          "logs:TagResource",
          "logs:UntagResource",
          "rds:AddTagsToResource",
          "rds:CreateDBSubnetGroup",
          "rds:DeleteDBSubnetGroup",
          "rds:ModifyDBSubnetGroup",
          "rds:RemoveTagsFromResource",
          "secretsmanager:CreateSecret",
          "secretsmanager:DeleteSecret",
          "secretsmanager:PutSecretValue",
          "secretsmanager:RestoreSecret",
          "secretsmanager:TagResource",
          "secretsmanager:UntagResource",
          "secretsmanager:UpdateSecret",
        ])
        Resource = "*"
      },
      {
        Sid      = "ReadStreamlitAuthSecretValue"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = local.streamlit_auth_secret_arn
      },
      {
        Sid    = "ManageLearningTaskRoles"
        Effect = "Allow"
        Action = [
          "iam:AttachRolePolicy",
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:DeleteRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PassRole",
          "iam:PutRolePolicy",
          "iam:TagRole",
          "iam:UntagRole",
          "iam:UpdateAssumeRolePolicy",
          "iam:UpdateRoleDescription",
        ]
        Resource = "arn:aws:iam::${var.target_account_id}:role/support-desk-learning-*"
      },
      {
        Sid    = "CreateRequiredServiceLinkedRoles"
        Effect = "Allow"
        Action = ["iam:CreateServiceLinkedRole"]
        Resource = [
          "arn:aws:iam::${var.target_account_id}:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS*",
          "arn:aws:iam::${var.target_account_id}:role/aws-service-role/elasticloadbalancing.amazonaws.com/AWSServiceRoleForElasticLoadBalancing*",
          "arn:aws:iam::${var.target_account_id}:role/aws-service-role/vpcorigin.cloudfront.amazonaws.com/AWSServiceRoleForCloudFrontVPCOrigin*",
        ]
        Condition = {
          StringEquals = {
            "iam:AWSServiceName" = [
              "ecs.amazonaws.com",
              "elasticloadbalancing.amazonaws.com",
              "vpcorigin.cloudfront.amazonaws.com",
            ]
          }
        }
      },
    ]
  })
}
