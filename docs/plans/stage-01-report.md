# Stage 1: Coding session reports and summaries

## Slice 1.1

Implementation record (2026-11-08): added the typed question/draft boundaries,
`POST /questions`, a packaged Boardlight v1 lookup, and an OpenAI Agents SDK adapter.
The application admits one generation per process with a 45-second deadline.
Input/body, turn, tool-call, and output-token limits are enforced in code;
provider retries are disabled. Citations must identify evidence actually returned
by the tool. Drafts remain unreviewed; these checks establish source identity,
not semantic grounding. SDK traces are disabled and Responses requests set
`store=False`. See the [local run/configuration path](../../README.md#run-the-local-api)
and [learning conclusion](../learning/slice-1.1.md).

Design revision (2026-11-08): separated health and question routers, kept business
values in the domain and the use-case request in the application layer, and added
HTTP-only health and stable error schemas. Corrected the bounded ASGI request stream,
declared Starlette directly, added an API-owned generic lifespan, and registered the
OpenAI client only for enabled inference. Composition settings are immutable Pydantic
values, direct asynchronous tests use pytest-asyncio, stable agent configuration is
reused, executable limits are centralized, and architecture checks are recursive.
Focused verification was added for these contracts. The final evidence below
supersedes the earlier verification runs.

Final local verification (2026-11-09): the capped Black check completed with all
40 files unchanged. isort, Ruff, strict mypy, lock consistency, OpenAPI generation,
source/wheel builds, `git diff --check`, and 41 deterministic tests passed. The
tests cover API contracts, composition, body-stream replay, domain and application
invariants, generic resource lifecycle, architecture rules, and the actual Agents
SDK loop with synthetic provider responses. The suite passed outside the restricted
sandbox, where its first asynchronous HTTP test stalls.

The current non-root image built as
`sha256:682a945b758c550e055e97c9bc365393c1b9b29805a7b3935c0e6878e965bad2`.
Its Docker health check, liveness endpoint, unconfigured readiness and question
responses, runtime UID 10001, packaged evidence, and paid-smoke module passed a
local smoke check. The wheel contains both route modules, the smoke runner, and all
four evidence documents.

Follow-up local verification (2026-11-09): after adding sanitized provider usage
diagnostics and the fixed paid-smoke runner, 43 deterministic tests, isort, Ruff,
strict mypy, and `git diff --check` passed. Black reformatted the two new modules
but exited at the mandatory 30-second cap, so it was not retried and remains
incomplete for that invocation. The user subsequently completed Black manually and
reported that it fixed one formatting issue. Lock consistency, OpenAPI generation,
source/wheel builds, and the rebuilt container smoke also passed.

The approved paid smoke used
`gpt-5.4-mini-2026-03-17` for exactly two authored questions: Free board capacity
(expect `BL-PLANS` v1) and refund policy (expect insufficient evidence).
The total experiment budget was USD 0.25; at most six model calls and 6,144
output tokens across both attempts, with no automatic retries. Stop after the two
attempts, including failures; further attempts need a new agreed budget. This is
an experiment budget, not an account-level spending control. The
[official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
lists Responses, function calling, and structured outputs, with standard input/
output prices of USD 0.75/4.50 per million tokens as checked on 2026-11-08.
Only authored questions and product evidence go to OpenAI; SDK tracing stays off.

Smoke execution (2026-11-09): `.env.smoke` passed existence, mode-`600`, and Git
ignore checks without its contents being read. The board-capacity attempt failed
with `APIConnectionError` and was not retried. Separate unauthenticated curl and
synthetic-key SDK checks then confirmed general OpenAI connectivity. The remaining
refund-policy attempt completed far enough to build live provider/tool diagnostics,
then failed a runner postcondition with `RuntimeError`. The runner emitted results
only after postconditions, so its draft, response IDs, usage, and cost were lost.
No secret appeared in output, and no further paid attempt was made.

The runner now flushes each sanitized case record before validating postconditions
and supports selecting one remaining authored case without retrying earlier work.
A regression test verifies that a completed case remains recoverable when a
postcondition fails.

Paid follow-up (2026-11-09): the approved USD 0.10 experiment ran each authored
case once with no retries. Both used one lookup and two model calls. Board capacity
returned `answered`, cited and read only `BL-PLANS`, and passed human review and all
postconditions. It used 1,801 input and 74 output tokens in 7.983 seconds, for an
estimated USD 0.00168375.

Refund policy returned `insufficient_evidence`, invented no eligibility or refund
rule, and appropriately requested authoritative clarification. It read and cited
`BL-PLANS` and `BL-UPGRADES`, rather than the authored expectation of no evidence,
so the strict postcondition failed. Human review accepts the safe evidence-gap
answer but records a semantic citation limitation: those sources show what the
agent inspected but do not prove that no refund policy exists. It used 2,158 input
and 169 output tokens in 3.872 seconds, for an estimated USD 0.00237900.

The follow-up totaled four model calls, 3,959 input tokens, no cached input, 243
output tokens, no reported reasoning tokens, and estimated cost USD 0.00406275.
SDK tracing remained disabled, Responses storage was false, and no credential
appeared in output. Live SDK/tool compatibility, bounded execution, structural
grounding, usage capture, and safe insufficient-evidence behavior are verified.
The semantic citation mismatch becomes a baseline case for Slice 1.8 rather than
being hidden or treated as proof of grounding quality. Slice 1.1 is complete.

## Slice 1.2

### Implementation

Implementation record (2026-11-09): added a Streamlit question form, draft and
evidence display, explicit unreviewed labeling, and safe empty-input, API, transport,
and invalid-contract failures. A typed HTTP client validates requests and parses
FastAPI results into the existing domain draft. The UI imports no repository or
agent adapter. Locked Streamlit and HTTPX runtime dependencies and two-service local
Compose orchestration provide API startup ordering and health checks.

### Deterministic and static verification

Streamlit AppTest followed the authored Free-board question through the form and
verified the draft and `BL-PLANS` evidence display. Client tests covered valid
results, declared API errors, transport failure, and invalid response payloads. All
55 deterministic tests passed outside the restricted sandbox, where the existing
asynchronous HTTP test stalls. isort, Ruff, strict mypy, lock consistency, Compose
configuration, source/wheel builds, relative-link verification, and
`git diff --check` passed.

Final formatting verification (2026-11-09): the required capped command completed
within 30 seconds and reported all 50 files unchanged:

```text
timeout 30s env UV_CACHE_DIR=<writable-cache> uv run black --check src tests
All done! ✨ 🍰 ✨
50 files would be left unchanged.
```

### Compose and browser verification

The networked Compose build completed from the locked dependency set. Compose waited
for the API health check before starting Streamlit. Both containers became healthy,
ran as the image's non-root `app` user, and exposed only localhost ports. The verified
image identities were:

- API: `sha256:204da36d9ca8e02113152893666127a3cef7492428b2f9639912b79e8b15b4c1`
- UI: `sha256:400c8d41944958ffd7b2367da0883dc896a1285fd0a29890c784e16754233851`

`GET /health/live` returned `{"status":"alive"}`, and Streamlit's health endpoint
returned `ok`. With inference explicitly disabled, the authored question returned
HTTP 503 with the declared `generation_unavailable` code and safe message. A real
headless Chromium session submitted the same question through the Compose-served UI
and displayed that safe message.

Browser review also used a temporary deterministic API adapter to verify the success
display without another paid model call. It returned the authored Free-workspace
capacity guidance with `BL-PLANS` v1, and the UI displayed the unreviewed warning,
draft, and evidence identity. The adapter and browser helper were temporary
verification tools and are not product dependencies.

Initial question form:

![Slice 1.2 question form](assets/slice-1.2/question-form.png)

Successful deterministic draft and evidence:

![Slice 1.2 answered draft](assets/slice-1.2/answered-draft.png)

Safe response from the inference-disabled Compose API:

![Slice 1.2 safe API failure](assets/slice-1.2/safe-api-failure.png)

No model call was made and no additional inference cost was incurred during Slice
1.2 verification.

### Learning conclusion

The typed HTTP boundary lets Streamlit distinguish safe application failures from
transport and contract failures without depending on repositories or agent internals.
Deterministic tests establish boundary behavior; the Compose and browser checks add
evidence for packaging, startup ordering, service connectivity, and operator-visible
behavior. See the [learning record](../learning/slice-1.2.md). Slice 1.2 is complete.

## Slice 1.3

Decisions recorded on 2026-11-11: use the existing AWS Organizations management
account in `us-east-1` as a bounded learning-environment exception, Terraform with
remote S3 state, GitHub OIDC, Cognito hosted login with Google and an explicit operator
group, and a default CloudFront HTTPS URL backed by a VPC origin, internal Application
Load Balancer, and one ECS/Fargate service. Reserve private database subnets for later
private RDS PostgreSQL. Treat USD 10 as a temporary deployment-experiment budget, not
an enforced service limit. The user completed the account budget alert, installed
Terraform 1.17.1, and verified temporary caller identity through the
`support-desk-bootstrap` Identity Center profile. No workload resources have been
provisioned. See [ADR 0001](../decisions/0001-manage-aws-infrastructure-with-terraform.md),
[ADR 0002](../decisions/0002-use-cognito-with-google-for-operator-access.md), and
[ADR 0003](../decisions/0003-use-a-cloudfront-vpc-origin-for-domain-free-https.md),
and [ADR 0004](../decisions/0004-use-the-existing-management-account-for-the-learning-deployment.md).

Implement Slice 1.3 in these review units:

1. Bootstrap encrypted, versioned, locked Terraform state and the restricted GitHub
   OIDC roles.
2. Add application authorization and deterministic authorized/unauthorized tests.
3. Add reviewable networking, ECR, ECS, load-balancing, CloudFront, Cognito, secret,
   health-check, and future database-subnet infrastructure.
4. Add immutable image build/deployment, smoke, rollback, and teardown workflows and
   guidance.
5. After explicit live-execution approval, provision, configure Google federation,
   deploy, verify, roll back, and tear down within the agreed budget.

### Bootstrap implementation

Local preparation on 2026-11-11 added the account-guarded Terraform bootstrap for
the encrypted, versioned, non-public S3 state bucket and repository-scoped GitHub
OIDC roles. The roles initially have state-only permissions; service permissions
wait for the concrete infrastructure review. Separate protected GitHub environments
gate state-reading plans and infrastructure applies so untrusted pull-request code
cannot obtain state credentials.

Terraform formatting and validation passed with Terraform 1.17.1 and locked AWS
provider 6.72.0. Two mocked Terraform tests passed, covering bounded resource names,
state retention, versioning, GitHub role names, and reuse of an existing account-level
GitHub provider. Provider download required network access; validation and tests made
no AWS API calls. An authenticated saved plan proposed the expected 11 additions with
no changes or deletions. The ignored inputs and plan are owner-readable only.

Live execution on 2026-11-11 applied that saved plan with 11 additions, no changes,
and no deletions. Terraform then migrated the bootstrap state from the ignored local
file to `bootstrap/terraform.tfstate` in the encrypted, versioned S3 bucket using
native lockfile locking. Remote state listed all 11 resources, and a fresh refresh
reported no configuration drift. The retained ignored migration backup is
owner-readable only. IAM has no direct charge; the small S3 state object and requests
begin minimal usage-based billing within the agreed budget.

### Authentication and authorization implementation

Local implementation on 2026-11-11 added a domain authentication contract, an
application-owned `operators` group decision, and infrastructure adapters for local
development and Cognito access tokens. The Cognito adapter verifies the RS256
signature, expiry, issuer, app client, access-token use, subject, and bounded group
claims. The API fails closed when authentication is unavailable, returns stable 401
and 403 responses, and keeps liveness public. Local Compose explicitly uses the
synthetic local operator; shared deployment must use Cognito.

PyJWT and its cryptography support are locked as runtime dependencies. The focused
authentication suite passed 13 tests and the complete deterministic suite passed all
77 tests. isort, Ruff, and strict mypy passed. Black identified one formatting change
before reaching its 30-second cap; the file was reformatted with the compatible Ruff
formatter, and Black was not retried as required after a timeout. Cognito and Google
resources and browser login remain for the infrastructure review unit.

### Application-platform infrastructure

Local implementation on 2026-11-12 added the account-guarded application stack under
`infra/platform`. It defines six subnets across two supported Availability Zone IDs:
private CloudFront-origin subnets for the internal ALB, public application subnets
for an explicitly addressed Fargate task, and private subnets plus a subnet group for
the later RDS PostgreSQL destination. There is no NAT gateway. Security groups admit
ALB traffic only from the CloudFront origin-facing prefix list and task traffic only
from the ALB on the Streamlit port; FastAPI remains task-local.

The stack also defines an immutable, scan-on-push ECR repository, one API/UI task
definition pinned by image digest, an ECS service with deployment-circuit-breaker
rollback, seven-day CloudWatch logs, an internal ALB with Streamlit health checks,
a non-caching CloudFront VPC origin, a closed-sign-up Cognito user pool and operator
group, and a recoverable Secrets Manager container. Terraform creates no secret
version, so the OpenAI credential does not enter configuration or state. The service
desired count defaults to zero and is capped at one. Google federation, browser
authorization-code session handling, secret population, and task startup remain
explicit prerequisites rather than claimed capabilities.

Terraform 1.17.1 formatting and validation passed with locked AWS provider 6.73.0.
Two mocked tests passed, covering the subnet topology, stopped-by-default and one-task
service limits, immutable repository, exact image-digest construction, internal ALB,
disabled dynamic caching, closed public sign-up, and secret recovery window. The
provider download was networked; validation and mocked tests made no AWS API calls.
No platform plan was produced against the live account, and no application resource
was provisioned. Delivery operations are recorded below; the browser authentication
session remains necessary for the live Cognito journey.

### Delivery operations

Local implementation on 2026-11-12 added a manually dispatched, environment-gated
GitHub workflow for read-only planning, stopped-service provisioning, immutable
commit-image deployment, prior-digest rollback, retained-platform stop, and confirmed
teardown. It uses short-lived OIDC credentials and account checks. Deploy writes the
GitHub environment's OpenAI credential to the pre-created Secrets Manager container
without printing it; Terraform state still contains no secret value. Release tags
are immutable and retries reuse the existing digest. Teardown requires an exact
confirmation and explicitly deletes retained images before the non-force-deletable
repository.

The bootstrap roles now have separate read-only plan and enumerated apply policies.
IAM role management remains restricted to the platform's task-role names; other
platform APIs with no consistent resource-level authorization use explicit actions
with the protected GitHub environment and provider account guard as controls. A local
bootstrap apply is required before the workflow can use these permissions.

A bounded standard-library deployment smoke checks the HTTPS entry point, exact
Streamlit health body, and application root without authenticating or invoking a
model. Deterministic tests cover healthy, unsafe-URL, unhealthy, and transport-failure
paths. This does not satisfy the live authenticated journey or unauthorized API
evidence. Google federation and browser token forwarding remain prerequisites to
starting the service.

Local verification passed Terraform formatting and validation for both stacks, two
bootstrap mocked tests, two platform mocked tests, workflow YAML parsing, isort,
Ruff, strict mypy across 59 files, all 83 deterministic tests, relative-link checks,
and `git diff --check`. The required Black command identified the new smoke module
for reformatting but reached the 30-second cap, so it was not retried; Ruff's
Black-compatible formatter applied that change and the subsequent static checks
passed. No workflow was dispatched and no live resource, secret, image, or state was
changed during this unit.

OIDC correction (2026-11-13): the first protected plan workflow reached AWS but STS
rejected its web-identity token. CloudTrail showed that GitHub issued the repository's
new immutable subject format with numeric owner and repository IDs, while the role
trusted the legacy name-only subject. The bootstrap now validates and includes both
public immutable IDs in the plan and apply trust policies. Mocked tests pin the exact
repository-and-environment subjects and reject malformed IDs. Applying this correction
must update only the two role trust policies before the workflow is retried.
