# ADR 0004: Use the existing management account for the learning deployment

**Status:** Accepted

## Context

The current AWS organization contains one account, which is its management account.
Creating a separate member account is outside the project's practical setup scope.
The Stage 1 deployment is temporary, synthetic, and limited to a USD 10 experiment.

## Decision

Deploy the Stage 1 learning workload into the existing AWS Organizations management
account in `us-east-1`. Use a separate IAM Identity Center user with MFA and temporary
bootstrap administration; do not create access keys. After bootstrap, use restricted
GitHub OIDC, task, and operator roles for routine access.

Prefix resource names with `support-desk` and tag applicable resources with
`Project=SupportDesk` and `Environment=learning`. Retain account-wide budget alerts,
review each Terraform plan, and tear down temporary application resources after live
verification.

## Rationale

This choice avoids additional account onboarding while retaining short-lived human
credentials and explicit workload roles. It accepts a larger blast radius and the
absence of organization policy isolation in the management account. It is suitable
for this bounded learning deployment and is not the target pattern for a production
workload.
