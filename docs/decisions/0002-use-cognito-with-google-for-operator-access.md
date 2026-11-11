# ADR 0002: Use Cognito with Google for operator access

**Status:** Accepted

## Context

The deployed application needs operator authentication without owning passwords or
password-reset workflows. Authentication must not replace application authorization.

## Decision

Use an Amazon Cognito user pool with its AWS-hosted login domain and Google as the
only initial external identity provider. Use the OAuth authorization-code flow with
exact callback and sign-out URLs. Do not enable public Cognito sign-up or implicit
token grants.

Authorize operators through a Cognito `operators` group. The FastAPI application
validates token signature, issuer, client, expiry, and required claims, then enforces
group membership. Streamlit carries the authenticated operator session but is not
the authorization boundary. The Google OAuth application starts in testing mode
with only agreed test users.

## Rationale

Cognito standardizes Google identities into AWS-issued tokens and avoids a custom
credential store. A dedicated group provides explicit, revocable application access
without relying on mutable email addresses. API enforcement protects the use case
when the UI or network entry point is bypassed.
