# Stage 1: Walking Skeleton

Status: reviewed and approved, subject to further review questions. Repository
preparation and units A/B are done. Slice 1.1 implementation and deterministic
verification are done. The paid follow-up verified live inference and captured one
semantic citation limitation for the later evaluation baseline. The user completed
Black manually and fixed one formatting issue. Slice 1.1 is done. Verification
evidence is recorded below. The breakdown below makes review units smaller while
preserving the approved outcome and release gate.

## Outcome and boundaries

An operator asks about a fictional SaaS product, receives an evidence-based draft,
saves it, and reopens it in a live environment. Introduce OpenAI Agents SDK first;
LangChain/pgvector, LangGraph, and CrewAI arrive in their planned stages. Use a small
fixed, authored reference pack. Clearly label generated answers as unreviewed drafts.

Primary learning is the agent/tool loop, evidence-based behavior, evaluation,
telemetry, and delivery. Keep infrastructure explanations focused on consequential
choices. Use one provider path initially; choose the model after checking current
capabilities, SDK compatibility, and cost.

## Review and delivery discipline

Implement one review unit at a time. Split a unit further when it introduces several
independent concepts; file count alone is not the review criterion. Each feature
slice adds a usable improvement, appropriate verification, and a deployable increment.
Prepare deployment artifacts with the local path, then deploy early in Slice 1.3.
Update the deployment after subsequent slices when cloud execution is authorized.

For each unit, state a hypothesis, explain the main learning concept, record
verification evidence, and capture a concise conclusion. Complete release evidence
remains required even when an individual change is small.

## Preparation A: Establish Python tooling and CI

Configure packaging, uv lock, Black, isort, Ruff, mypy, pytest, and pull-request CI
for `master`. Verify Python/SDK compatibility before selecting dependency versions;
add runtime dependencies only as needed. Create packages with concrete responsibilities.

Verification: clean locked install and passing applicable checks; default tests
need no model keys. Cap Black at 30 seconds and run other checks independently.
Document the canonical development path only after verifying it.

Verification record (2026-11-08): clean `uv sync --locked` into a fresh environment,
isort, Ruff, strict mypy, the isolated package-import test, source/wheel builds,
and an isolated wheel installation/import passed on Python 3.12.3 with uv 0.12.7.
The lockfile consistency check passed. Black reported both files unchanged but
exited with status 124 at the 30-second cap and was not retried locally. The user
subsequently committed preparation A and reported all GitHub CI checks green,
including Black, with steps completing in about 10 seconds. Preparation A is done.

Compatibility check: PyPI metadata for `openai` 3.46.0 and `openai-agents` 0.24.0
requires Python >=3.10. Retain Python 3.12; verify APIs and full dependency resolution
when adding runtime SDKs. This unit adds development dependencies only.

Learning hypothesis: locked installation and an import from outside the repository
catch packaging errors before framework work begins. The clean install, isolated
import test, and distribution builds support that approach. The reported successful
CI run completes verification; the local Black timeout remains an environment
limitation to keep distinct from a formatting failure.

## Preparation B: Define the product evidence

Choose the fictional SaaS product and author a small versioned reference pack with
stable source identifiers. Cover plans, upgrade behavior, account access, and basic
troubleshooting. Include answerable and unanswerable example questions with expected
evidence. Expand these into the evaluation baseline later.

Verification: manually check that stated product rules are consistent and expected
answers are supported. This pack becomes the input for the first tool and tests.
Preparation A and B establish inputs and tooling; they do not ship an application.

Status: done. The user accepted Boardlight, a fictional team task-board SaaS.
The [reference pack](../product/boardlight/README.md) contains four sources at
version 1 with stable IDs, and eight example questions with expected evidence or
explicit gaps. Reviewed limits, workspace subscription scope, activation timing,
access, and troubleshooting for consistency; checked links and evidence targets.
No model runs or account records were needed.

Learning hypothesis: explicit workspace rules and evidence gaps should help separate
general guidance from account-specific conclusions. Comparing the capacity and
upgrade-guidance examples with the payment-status and refund questions shows the
intended distinction in the authored material. Model adherence remains unmeasured;
use these examples to check the first agent in Slice 1.1 and seed later evaluations.

## Slice 1.1: Generate a grounded answer through the API

Implement typed domain/application boundaries, a bounded reference lookup tool,
an Agents SDK adapter, and a FastAPI endpoint. Return a structured draft with source
references or an insufficient-evidence result. Use one bounded request at a time.
Enforce request, turn, token, time, and tool limits in code; bound retries.

Before real inference, choose the initial model, explicit run budget, and framework
trace/export policy. Available credits are not permission for unspecified spending.

Learning: inspect the actual tool call/result and explain the tool/schema boundary.
Verification: deterministic fake-agent API tests, valid references, timeout/invalid
argument handling, and an explicitly enabled budgeted model smoke run. Prepare a
container and health/readiness checks for this API increment.

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

## Slice 1.2: Ask a question through Streamlit

Add the question form, draft/evidence display, and useful failure messages.
Streamlit calls FastAPI through typed interfaces. Add local Compose orchestration
and verify the UI-to-API journey.

Learning: follow one request across UI, application, and agent boundaries.
Verification: API contract checks and a local UI demonstration with authored inputs;
include screenshots in review. Keep the first model run explicitly enabled.

## Slice 1.3: Deploy the question-answer journey

Establish infrastructure as code, image build/push, GitHub OIDC, secrets, operator
access, HTTPS, and ECS/Fargate deployment. Enforce authorization in application
code. Document smoke verification, immutable image identities, rollback, and teardown.

Before provisioning, agree the AWS account/region, infrastructure tool, access
mechanism, data flow, and cloud budget. Prepare reviewable infrastructure before
requesting live execution. Include a durable PostgreSQL destination in the design
before adding persistence in the next slice.

Learning: trace a release from commit to running image and distinguish spending
alerts from enforced application limits.
Verification: unauthorized requests fail; live ask/draft journey, health checks,
smoke test, and rollback demonstration pass. Record remaining deployment limitations.

## Slice 1.4: Persist interactions and generation attempts

Define saved success/failure data, retry identity, duplicate-submission behavior,
and retention. Add repository contracts, Db-prefixed SQLAlchemy adapters, a reviewed
Alembic baseline, and local PostgreSQL. Keep transactions outside model calls.

Learning: explain provenance and failure semantics around a nondeterministic call.
Verification: disposable-PostgreSQL repository and migration tests; CI starts its
required database explicitly. Default tests require no unstated services or keys.

## Slice 1.5: Save and reopen through the UI

Expose saved questions and drafts through API and UI. Provision the agreed durable
cloud PostgreSQL storage and deploy the complete ask/save/reopen journey.

Learning: distinguish a support interaction from the later durable case lifecycle.
Verification: API save/reopen and duplicate-submission checks; persisted results
survive application task replacement; secrets are absent from stored records.

## Slice 1.6: Trace the agent journey in Phoenix

Instrument and correlate application, agent, and tool spans. Provision local Phoenix
and the agreed cloud collection/storage arrangement. Document trace content,
redaction, retention, access, destinations, and export toggles. Configure additional
framework exporters deliberately.

Learning: use a real trace to explain a failed or ungrounded answer.
Verification: inspect a correlated trace, exercise a tool error and unavailable
collector, and verify redaction/access. Telemetry failure must preserve successful
business outcomes. Deploy and demonstrate.

## Slice 1.7: Add operational metrics and a dashboard

Add Prometheus metrics and Grafana for requests, latency, errors, tool failures,
and available model usage/estimated cost. Keep labels bounded; record the pricing
basis and estimation limitations. Specify durable cloud telemetry storage separately
from local Compose volumes.

Learning: distinguish traces, metrics, logs, and billing ground truth.
Verification: inspect the dashboard under success/failure requests; verify bounded
labels and collector-outage behavior. Deploy and demonstrate.

## Slice 1.8: Establish the evaluation baseline

Expand the versioned examples to cover answerable, unanswerable, ambiguous, and
adversarial questions. Add deterministic reference/schema/tool checks, a human
review rubric, and RAGAS-based grounded-answer assessment where appropriate.
Record prompt/model/judge configuration, evidence versions, latency, and estimated
cost. Provide a separately enabled, budgeted evaluation command/workflow.

Learning: explain what each metric establishes and where human review is needed.
Verification: repeatable baseline results and one demonstrated grounding failure
or judge/human disagreement. Default CI makes no real model calls.

## Slice 1.9: Compare and improve one prompt

Run a controlled prompt comparison against the baseline. Calibrate judge output
against human review before choosing blocking quality thresholds. Ship a justified
prompt improvement with measured evidence, or record why the baseline was retained.

Learning: distinguish a plausible improvement from evidence of better behavior.
Verification: versioned comparison inputs/configuration/results, cost, limitations,
and a concise learning conclusion. Retrieval ranking metrics wait for Stage 2.

## Slice 1.10: Validate the complete release

Exercise provider timeout, invalid tool arguments, duplicate submission, application
restart, and telemetry outage. Confirm enforced limits and bounded retries. Finish
cost, access, data-flow, recovery, rollback, and teardown guidance. Add a small
operator-facing failure/retry improvement if testing exposes one. Reuse passing
checks unless changes justify rerunning them.

Verification: live ask/save/reopen journey; persisted data survives restart; a real
trace and dashboard; evaluation evidence; deployment smoke and rollback demonstration.
Document remaining limitations and learning conclusions.

## Completion evidence

Record the release commit/image identity, validation results, deployment smoke result,
evaluation report location/configuration, privacy/cost decisions, and concise learning
notes. Do not commit sensitive traces or secrets. Stage 1 is complete only after its
master-plan gate is demonstrated. Plan Stage 2 slices after reviewing those results.
