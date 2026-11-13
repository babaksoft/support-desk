# Stage 1: Walking Skeleton

**Status: In progress**

Status: reviewed and approved, subject to further review questions. Repository
preparation and units A/B are done. Slice 1.1 implementation and deterministic
verification are done. The paid follow-up verified live inference and captured one
semantic citation limitation for the later evaluation baseline. The user completed
Black manually and fixed one formatting issue. Slice 1.1 is done. Verification
for Slice 1.2 is also complete. Detailed implementation and verification records
are kept in the [Stage 1 report](stage-01-report.md). The breakdown below makes
review units smaller while preserving the approved outcome and release gate.

Slice 1.3 reviewable application infrastructure and delivery operations are
implemented and locally verified. No application-platform resource has been
provisioned. Applying the expanded GitHub permissions, browser session handling,
Google federation, live deployment, smoke, rollback, and teardown remain pending.

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

**Status: Complete**

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

**Status: Complete**

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

**Status: Complete**

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

## Slice 1.2: Ask a question through Streamlit

**Status: Complete**

Add the question form, draft/evidence display, and useful failure messages.
Streamlit calls FastAPI through typed interfaces. Add local Compose orchestration
and verify the UI-to-API journey.

Learning: follow one request across UI, application, and agent boundaries.
Verification: API contract checks and a local UI demonstration with authored inputs;
include screenshots in review. Keep the first model run explicitly enabled.

## Slice 1.3: Deploy the question-answer journey

**Status: In progress**

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
