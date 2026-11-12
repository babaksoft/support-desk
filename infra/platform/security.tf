data "aws_ec2_managed_prefix_list" "cloudfront_origin_facing" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_security_group" "load_balancer" {
  name        = "${local.name}-load-balancer"
  description = "Accepts HTTP only from CloudFront origin-facing addresses."
  vpc_id      = aws_vpc.application.id

  tags = {
    Name = "${local.name}-load-balancer"
  }
}

resource "aws_vpc_security_group_ingress_rule" "cloudfront_to_load_balancer" {
  description       = "CloudFront VPC-origin HTTP traffic."
  from_port         = 80
  ip_protocol       = "tcp"
  prefix_list_id    = data.aws_ec2_managed_prefix_list.cloudfront_origin_facing.id
  security_group_id = aws_security_group.load_balancer.id
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "load_balancer_to_ui" {
  description                  = "Streamlit traffic to the application task."
  from_port                    = 8501
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.task.id
  security_group_id            = aws_security_group.load_balancer.id
  to_port                      = 8501
}

resource "aws_security_group" "task" {
  name        = "${local.name}-task"
  description = "Accepts Streamlit traffic only from the internal load balancer."
  vpc_id      = aws_vpc.application.id

  tags = {
    Name = "${local.name}-task"
  }
}

resource "aws_vpc_security_group_ingress_rule" "load_balancer_to_task" {
  description                  = "Streamlit traffic from the internal load balancer."
  from_port                    = 8501
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.load_balancer.id
  security_group_id            = aws_security_group.task.id
  to_port                      = 8501
}

resource "aws_vpc_security_group_egress_rule" "task_outbound" {
  description       = "Bounded task outbound access through its public IPv4 address."
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  security_group_id = aws_security_group.task.id
}

