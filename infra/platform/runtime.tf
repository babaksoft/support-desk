resource "aws_cloudwatch_log_group" "application" {
  name              = "/support-desk/learning/application"
  retention_in_days = 7
}

resource "aws_iam_role" "task_execution" {
  name        = "support-desk-learning-task-execution"
  description = "Pulls the application image, writes logs, and reads the runtime secret."
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "task_execution_secret" {
  name = "support-desk-runtime-secrets"
  role = aws_iam_role.task_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadRuntimeSecrets"
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          aws_secretsmanager_secret.openai_api_key.arn,
          aws_secretsmanager_secret.streamlit_auth.arn,
        ]
      },
    ]
  })
}

resource "aws_iam_role" "task" {
  name        = "support-desk-learning-task"
  description = "Runtime identity for the Support Desk application task."
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_ecs_cluster" "application" {
  name = local.name

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "application" {
  cluster_name       = aws_ecs_cluster.application.name
  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    base              = 1
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

resource "aws_ecs_task_definition" "application" {
  family                   = local.name
  cpu                      = 512
  memory                   = 1024
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = local.image_uri
      essential = true
      cpu       = 256
      memory    = 512
      command = [
        "/app/.venv/bin/uvicorn",
        "support_desk.composition.api:build_app",
        "--factory",
        "--host=0.0.0.0",
        "--port=8000",
        "--workers=1",
        "--limit-concurrency=8",
        "--timeout-keep-alive=5",
        "--no-access-log",
      ]
      portMappings = [
        {
          name          = "api"
          containerPort = 8000
          protocol      = "tcp"
        },
      ]
      environment = [
        { name = "SUPPORT_DESK_AUTH_MODE", value = "cognito" },
        { name = "SUPPORT_DESK_COGNITO_CLIENT_ID", value = aws_cognito_user_pool_client.operators.id },
        { name = "SUPPORT_DESK_COGNITO_ISSUER", value = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.operators.id}" },
        { name = "SUPPORT_DESK_ENABLE_INFERENCE", value = "1" },
        { name = "SUPPORT_DESK_MODEL", value = var.model },
        { name = "SUPPORT_DESK_OPERATOR_GROUP", value = local.operator_group },
      ]
      secrets = [
        {
          name      = "OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.openai_api_key.arn
        },
      ]
      healthCheck = {
        command = [
          "CMD-SHELL",
          "/app/.venv/bin/python -c \"from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health/live', timeout=2)\"",
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 10
      }
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.application.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    },
    {
      name      = "ui"
      image     = local.image_uri
      essential = true
      cpu       = 256
      memory    = 512
      command = [
        "/app/.venv/bin/python",
        "-m",
        "support_desk.composition.ui_server",
      ]
      portMappings = [
        {
          name          = "ui"
          containerPort = 8501
          protocol      = "tcp"
        },
      ]
      environment = [
        { name = "SUPPORT_DESK_API_URL", value = "http://127.0.0.1:8000" },
        { name = "SUPPORT_DESK_COGNITO_CLIENT_ID", value = aws_cognito_user_pool_client.operators.id },
        { name = "SUPPORT_DESK_COGNITO_ISSUER", value = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.operators.id}" },
        { name = "SUPPORT_DESK_PUBLIC_URL", value = local.cloudfront_url },
        { name = "SUPPORT_DESK_UI_AUTH_MODE", value = "cognito" },
      ]
      secrets = [
        {
          name      = "SUPPORT_DESK_COGNITO_CLIENT_SECRET"
          valueFrom = "${aws_secretsmanager_secret.streamlit_auth.arn}:client_secret::"
        },
        {
          name      = "SUPPORT_DESK_SESSION_COOKIE_SECRET"
          valueFrom = "${aws_secretsmanager_secret.streamlit_auth.arn}:cookie_secret::"
        },
      ]
      dependsOn = [
        {
          containerName = "api"
          condition     = "HEALTHY"
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.application.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ui"
        }
      }
    },
  ])
}

resource "aws_lb" "application" {
  name                       = "support-desk-learning"
  internal                   = true
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.load_balancer.id]
  drop_invalid_header_fields = true
  enable_deletion_protection = false
  subnets = [
    aws_subnet.application["origin-1"].id,
    aws_subnet.application["origin-2"].id,
  ]
}

resource "aws_lb_target_group" "ui" {
  name        = "support-desk-learning-ui"
  port        = 8501
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.application.id

  deregistration_delay = 15

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 15
    matcher             = "200"
    path                = "/_stcore/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.application.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui.arn
  }
}

resource "aws_ecs_service" "application" {
  name                               = local.name
  cluster                            = aws_ecs_cluster.application.id
  task_definition                    = aws_ecs_task_definition.application.arn
  desired_count                      = var.service_desired_count
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 0
  health_check_grace_period_seconds  = 30
  launch_type                        = "FARGATE"
  platform_version                   = "LATEST"
  propagate_tags                     = "SERVICE"
  wait_for_steady_state              = true

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    assign_public_ip = true
    security_groups  = [aws_security_group.task.id]
    subnets = [
      aws_subnet.application["application-1"].id,
      aws_subnet.application["application-2"].id,
    ]
  }

  load_balancer {
    container_name   = "ui"
    container_port   = 8501
    target_group_arn = aws_lb_target_group.ui.arn
  }

  depends_on = [
    aws_ecs_cluster_capacity_providers.application,
    aws_iam_role_policy_attachment.task_execution,
    aws_iam_role_policy.task_execution_secret,
    aws_lb_listener.http,
  ]
}

