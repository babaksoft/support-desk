# ADR 0006: Serve the application through a public HTTPS load balancer

**Status:** Accepted

## Decision

Use the existing public `babaksoft.dev` Route 53 zone for
`support-desk.babaksoft.dev`. An internet-facing Application Load Balancer
terminates HTTPS with a DNS-validated ACM certificate and forwards to Streamlit.
Streamlit owns operator sign-in through Cognito and calls FastAPI over the
task-local network. The application stack owns its alias and certificate
validation records. The parent zone belongs to the shared domain.

## Rationale

The registered domain gives the load balancer a browser-trusted hostname and
stable Cognito callback. This removes the CloudFront distribution and VPC origin
from the application stack. The ALB becomes the public ingress, and security
groups restrict incoming task traffic to the Streamlit port from the ALB.
