# ADR 0001: Manage AWS infrastructure with Terraform

**Status:** Accepted

## Context

Stage 1 needs reviewable AWS infrastructure, repeatable deployment, rollback, and
teardown. GitHub Actions must deploy without stored long-lived AWS credentials.
Terraform state can contain sensitive infrastructure data and must not be committed.

## Decision

Use Terraform with pinned Terraform and AWS provider versions. Store remote state
in a dedicated, encrypted, versioned S3 bucket in `us-east-1`, with S3 lockfile
locking enabled. A small reviewed bootstrap unit creates the state storage before
the application stack uses it.

GitHub Actions uses OIDC to assume repository- and environment-scoped AWS roles.
Pull requests run formatting, validation, and plans without applying changes.
Deployment applies run from the protected `master` environment after review. Human
administration uses temporary credentials; no AWS access keys are stored in GitHub.

## Rationale

Terraform makes infrastructure changes and teardown reviewable across providers.
Remote state with versioning and locking supports recovery and prevents concurrent
writes. OIDC limits credential lifetime and keeps deployment credentials out of
repository and GitHub secrets.
