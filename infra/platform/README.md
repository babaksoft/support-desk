# Terraform application platform

This stack defines the temporary Slice 1.3 application platform in `us-east-1`.
It creates the network, immutable ECR repository, one stopped ECS/Fargate service,
internal load balancer, CloudFront VPC origin, Cognito user pool, runtime secret
container, log group, and private subnet group reserved for PostgreSQL. It does not
configure Google, put a credential into the secret, push an image, or start a task.

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

Local operations use the `support-desk-bootstrap` profile by default. A later GitHub
OIDC workflow must set `use_aws_profile = false` so the provider uses the temporary
ambient credentials assumed by the protected environment instead of looking for a
developer profile.

## Credentials and federation

Terraform creates the Secrets Manager container but deliberately creates no secret
version, keeping the OpenAI key out of configuration and Terraform state. Delivery
operations will document a non-printing, explicitly approved way to populate it
from the local smoke credential. Never pass the key as a Terraform variable.

The first infrastructure apply produces the exact CloudFront application callback
and Cognito Google callback outputs. Google federation and the Streamlit
authorization-code session must be configured before starting the service. Until
then, the Cognito app client has only the built-in provider enabled, public sign-up
is disabled, and no application operator should be created. The later federation
unit will enable Google as the operator identity provider and remove this transitional
provider configuration.

The ECR repository refuses recursive deletion. Teardown must first retain or
explicitly delete reviewed release images, then destroy the application stack.
The bootstrap state bucket remains until all dependent state has been handled.

