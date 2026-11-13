# Terraform application platform

This stack defines the temporary Slice 1.3 application platform in `us-east-1`.
It creates the network, immutable ECR repository, one stopped ECS/Fargate service,
internal load balancer, CloudFront VPC origin, Cognito user pool, runtime secret
containers, log group, and private subnet group reserved for PostgreSQL. It does not
create the external Google OAuth client, put an OpenAI credential into its secret,
push an image, or start a task.

## Architecture and cost boundary

CloudFront is the only public ingress. Its VPC origin reaches an internal ALB in
two private origin subnets. The ALB can reach only Streamlit on the task security
group. Streamlit calls FastAPI over the task-local loopback interface. A single
task can run in either of two public application subnets with an explicitly assigned
public IPv4 address for outbound model and AWS calls. There is no NAT gateway.
Two separate private subnets and an RDS subnet group reserve the accepted later
PostgreSQL destination; this stack provisions no database.

The default desired count is zero. An ALB, CloudFront distribution, public IPv4
address, Fargate task, logs, secrets, and image storage are billable when created or
used. The account budget alert is observational, not an enforced service limit.
Do not apply this stack without renewed live-execution approval under the agreed
USD 10 experiment budget.

## Review locally

Copy `backend.tfbackend.example` to the ignored `backend.tfbackend` and replace its
account placeholder. Copy `terraform.tfvars.example` to the ignored
`terraform.tfvars`, set the target account ID, and set an actual image digest before
a live deployment. The all-zero example digest is intentionally not deployable.

Initialize and run the non-mutating checks:

```bash
terraform -chdir=infra/platform init -backend=false
terraform -chdir=infra/platform fmt -check
terraform -chdir=infra/platform validate
terraform -chdir=infra/platform test
```

Initialize the remote backend only when preparing an authenticated reviewed plan:

```bash
terraform -chdir=infra/platform init -reconfigure \
  -backend-config=backend.tfbackend
terraform -chdir=infra/platform plan -out=platform.tfplan
terraform -chdir=infra/platform show platform.tfplan
```

The saved plan is ignored and can contain sensitive infrastructure values. Applying
it is a separate explicitly approved live action.

Local operations use the `support-desk-bootstrap` profile by default. The GitHub
OIDC workflow sets `use_aws_profile = false`, so Terraform uses the temporary ambient
credentials assumed by the protected environment instead of looking for a developer
profile.

## Credentials and federation

Terraform creates the Secrets Manager container but deliberately creates no secret
version, keeping the OpenAI key out of configuration and Terraform state. Delivery
operations will document a non-printing, explicitly approved way to populate it
from the local smoke credential. Never pass the key as a Terraform variable.

The first stopped-service `provision` operation produces the exact callbacks. Before
applying the federation update, create a Google Auth Platform web client in testing
mode with only the agreed test users and register the exact
`cognito_google_callback_url` output as its authorized redirect URI. In the existing
Cognito user pool, add Google with scopes `openid email profile`, map `email` and
`email_verified`, and keep the Google client secret in Google and Cognito consoles;
do not put it in source, Terraform inputs, or command output.

The reviewed federation update replaces the transitional public Cognito client with
a confidential client, registers the `cognito_callback_url` output ending in
`/oauth2callback`, and enables only Google. Terraform generates the Cognito client
secret and Streamlit cookie secret into encrypted remote state and a dedicated
recoverable Secrets Manager value; neither is rendered by the plan. Streamlit keeps
the authorization-code session and forwards only the Cognito access token to the
task-local API. Public Cognito sign-up remains disabled.

The first successful Google login creates the federated Cognito user. Add that exact
user to the existing `operators` group, then sign out and back in so the new access
token contains the authorization claim. Group membership, not the Google email
address, grants application access.

The ECR repository refuses recursive deletion. Teardown must first retain or
explicitly delete reviewed release images, then destroy the application stack.
The bootstrap state bucket remains until all dependent state has been handled.

## Delivery workflow

The manually dispatched [AWS platform workflow](../../.github/workflows/aws-platform.yml)
uses only protected GitHub environments and short-lived OIDC credentials. Configure
the `AWS_ACCOUNT_ID` environment variable in both `learning-plan` and `learning`.
Configure `OPENAI_API_KEY` as a secret only in `learning`; the deploy job writes it
to the existing Secrets Manager container through an owner-readable temporary file
and does not print it. Keep required reviewers and master-only deployment branches
on both environments.

Operations are deliberately separate:

- `plan` reads remote state and renders a plan for a supplied image digest and task
  count without changing AWS.
- `provision` applies the stopped platform with the all-zero placeholder digest. It
  creates the ECR repository and callback outputs but starts no task.
- `deploy` builds the current commit as `git-<commit>`, reuses that immutable tag on
  a retry, records the ECR digest, populates the runtime secret, and applies exactly
  that digest with one task.
- `rollback` verifies a supplied prior digest still exists, reapplies it, and waits
  for ECS steady state. The ECS deployment circuit breaker also rolls back a failed
  in-progress deployment to its last completed revision.
- `stop` resolves the currently configured digest and applies a desired count of
  zero while retaining the platform.
- `destroy` requires the exact `destroy-support-desk` confirmation, renders the
  destroy plan, deletes retained ECR images, and applies the plan. Image deletion is
  irreversible. The seven-day Secrets Manager recovery window and bootstrap state
  resources remain.

Deploy and rollback finish with a non-billable HTTPS/Streamlit reachability smoke.
That smoke does not authenticate, call FastAPI, or invoke a model. Live Google
federation, browser-session evidence, unauthorized API evidence, and the budgeted
ask/draft journey must be completed before this slice can claim live verification.

