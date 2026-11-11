# ADR 0003: Use a CloudFront VPC origin for domain-free HTTPS

**Status:** Accepted

## Context

The deployment needs browser-trusted HTTPS and Google OAuth callbacks without
registering a domain. An Application Load Balancer hostname or raw IP address cannot
receive a matching public certificate controlled by this project. The initial
deployment also has a USD 10 experiment budget.

## Decision

Use the default CloudFront `*.cloudfront.net` hostname and certificate as the public
entry point. CloudFront connects through a VPC origin to an internal Application
Load Balancer. The load balancer routes only to the Streamlit container in one ECS
service; Streamlit calls the colocated FastAPI container over the task-local network.
Disable caching for authenticated dynamic traffic and forward the request features
needed by Streamlit, including WebSocket upgrades.

Run one Fargate task across public application subnets with a public IP for bounded
outbound access, avoiding a NAT gateway. Security groups admit task traffic only
from the internal load balancer; the task has no direct public listener. Use two
Availability Zones for the load balancer and subnets, while accepting that one task
does not provide application high availability.

Reserve private database subnets for a later private Amazon RDS for PostgreSQL
destination. Do not provision RDS in Slice 1.3. Keep the deployment temporary,
monitor the agreed USD 10 account budget, and tear down application resources after
smoke and rollback verification.

## Rationale

CloudFront supplies a trusted AWS-generated HTTPS URL suitable for Cognito callbacks.
The VPC origin avoids exposing the load balancer and keeps origin traffic private.
A public task IP is a deliberate low-cost compromise for outbound model and AWS API
access; security groups prevent unsolicited inbound traffic. Deferring RDS preserves
the slice boundary and budget while fixing the later durable storage destination.
