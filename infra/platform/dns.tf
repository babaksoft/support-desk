resource "aws_acm_certificate" "application" {
  domain_name       = var.application_hostname
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "certificate_validation" {
  zone_id = var.hosted_zone_id
  name    = one(aws_acm_certificate.application.domain_validation_options).resource_record_name
  type    = "CNAME"
  ttl     = 60
  records = [one(aws_acm_certificate.application.domain_validation_options).resource_record_value]
}

resource "aws_acm_certificate_validation" "application" {
  certificate_arn         = aws_acm_certificate.application.arn
  validation_record_fqdns = [aws_route53_record.certificate_validation.fqdn]
}

resource "aws_route53_record" "application" {
  zone_id = var.hosted_zone_id
  name    = var.application_hostname
  type    = "A"

  alias {
    name                   = aws_lb.application.dns_name
    zone_id                = aws_lb.application.zone_id
    evaluate_target_health = false
  }

  depends_on = [aws_lb_listener.https]
}
