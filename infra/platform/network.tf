resource "aws_vpc" "application" {
  cidr_block           = "10.32.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = local.name
  }
}

resource "aws_internet_gateway" "application" {
  vpc_id = aws_vpc.application.id

  tags = {
    Name = local.name
  }
}

resource "aws_subnet" "application" {
  for_each = local.subnets

  availability_zone_id    = each.value.availability_zone_id
  cidr_block              = each.value.cidr
  map_public_ip_on_launch = false
  vpc_id                  = aws_vpc.application.id

  tags = {
    Name = "${local.name}-${each.key}"
    Tier = each.value.tier
  }
}

resource "aws_route_table" "public_application" {
  vpc_id = aws_vpc.application.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.application.id
  }

  tags = {
    Name = "${local.name}-public-application"
  }
}

resource "aws_route_table_association" "public_application" {
  for_each = {
    for key, subnet in local.subnets : key => subnet if subnet.public
  }

  route_table_id = aws_route_table.public_application.id
  subnet_id      = aws_subnet.application[each.key].id
}

resource "aws_db_subnet_group" "future_postgresql" {
  name        = "${local.name}-postgresql"
  description = "Private database subnets reserved for Stage 1 PostgreSQL."
  subnet_ids = [
    aws_subnet.application["database-1"].id,
    aws_subnet.application["database-2"].id,
  ]

  tags = {
    Name = "${local.name}-postgresql"
  }
}

