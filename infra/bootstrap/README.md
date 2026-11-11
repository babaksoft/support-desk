# Terraform bootstrap

This unit prepares remote Terraform state and narrowly trusted GitHub Actions roles.
It does not create the application network, runtime, authentication, or database.

## Safety boundaries

- The AWS provider refuses any account other than `target_account_id`.
- The local profile uses temporary IAM Identity Center credentials.
- The S3 bucket blocks public access, rejects non-TLS access and SSE-C uploads,
  encrypts objects with SSE-S3, retains versions, and refuses recursive deletion.
- GitHub trust is limited to `babaksoft/support-desk`. Only the protected
  `learning-plan` environment may assume the state-reading plan role, and only the
  protected `learning` environment may assume the apply role.
- Both GitHub roles initially have state-only permissions. Later infrastructure
  permissions require a separate reviewed change.

Configure required reviewers and restrict deployment branches on the GitHub
`learning-plan` and `learning` environments before any workflow uses either role.
The AWS trust policy checks environment names but cannot configure GitHub's
protection rules. Requiring review for the plan environment prevents untrusted pull
request code from reading potentially sensitive Terraform state.

## Local preparation

Authenticate without creating long-lived access keys:

```bash
aws sso login --profile support-desk-bootstrap
```

Copy `terraform.tfvars.example` to the ignored `terraform.tfvars` file and replace
the placeholder with the target account ID. Do not commit that file.

Format and validate locally:

```bash
terraform -chdir=infra/bootstrap init
terraform -chdir=infra/bootstrap fmt -check
terraform -chdir=infra/bootstrap validate
terraform -chdir=infra/bootstrap test
```

These commands download the pinned provider but do not create AWS resources.

## Review before the first apply

Check whether the account already has a GitHub Actions OIDC provider:

```bash
aws iam list-open-id-connect-providers --profile support-desk-bootstrap
```

If the GitHub provider already exists, set `create_github_oidc_provider = false`
and set `github_oidc_provider_arn` in the ignored `terraform.tfvars` file. Never
paste credentials or SSO cache data into Terraform inputs.

Create a saved plan only after refreshing the SSO session:

```bash
terraform -chdir=infra/bootstrap plan -out=bootstrap.tfplan
terraform -chdir=infra/bootstrap show bootstrap.tfplan
```

The plan file is ignored because it can contain sensitive values. Applying it is a
separate, explicitly approved live action.

## State migration after apply

The first apply necessarily uses local state because it creates the remote backend.
Immediately afterward, copy `backend.tf.example` to `backend.tf`, replace its account
ID placeholder, and run `terraform init -migrate-state` with
`-backend-config=profile=support-desk-bootstrap`. Verify the migrated state before
removing the ignored local copy. The application stack will use
`learning/platform.tfstate` with native S3 lockfile locking.

The bucket and IAM resources incur no meaningful steady compute cost, but stored S3
data and requests are billable. Application teardown will retain this bootstrap
until all dependent Terraform state has been migrated or destroyed deliberately.
