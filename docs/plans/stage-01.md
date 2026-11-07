# Stage 1: Walking Skeleton

Status: initial draft; implementation has not started.

## Outcome and boundaries

An operator asks about a fictional SaaS product, receives an evidence-based draft,
saves it, and reopens it in a live environment. Introduce OpenAI Agents SDK only;
LangChain/pgvector, LangGraph, and CrewAI arrive in their planned stages. Use a small
fixed, authored reference pack rather than embedding search. Full case resolution,
account diagnostics, and FAQ proposals are not part of this stage.

Primary learning is the agent/tool loop, evidence-based behavior, evaluation,
telemetry, and delivery. Full-stack tasks receive the explanation necessary to
understand their boundaries without repeating introductory courses.

## Preparation: establish an executable foundation

Configure Python packaging, uv lock, development checks, testing, and pull-request
CI. Establish minimal domain/application/adapter boundaries and local PostgreSQL.
Create only needed packages. Verify SDK compatibility and current official APIs.
This is repository preparation, not a shipped feature.

Verification: clean locked install; familiar quality checks; deterministic tests
without model keys; CI explicitly starts any required database service. Add the
README's canonical development path only after running it successfully.

## Slice 1.1: Answer one product question and deploy it

Deliver a Streamlit question form calling FastAPI through a typed use case. A real
Agents SDK adapter uses one bounded reference lookup tool and returns a structured
draft with source references or an insufficient-evidence result. Clearly label the
output as an unreviewed draft. Use synthetic/authored inputs only.

Deploy this narrow path to ECS/Fargate early. Establish infrastructure as code,
image build/push, GitHub OIDC, secrets, access control, HTTPS, readiness, and smoke
verification. Document rollback and teardown. Start with one bounded request at a
time rather than a general long-running workflow engine.

Before cloud/model execution: settle model access, AWS destination, access mechanism,
telemetry export policy, and explicit budgets. Prepare code and infrastructure for
review before requesting any required live execution approval.

Learning: inspect the actual tool call and result; explain the tool/schema boundary
and how the agent is constrained. Authorization and size/turn/time limits belong
in code, not just prompts.

Verification: fake-agent API tests; real-model smoke run explicitly enabled; source
references exist in the fixed pack; an unanswerable question does not invent facts;
unauthorized requests fail; live journey works after deployment and rollback.

## Slice 1.2: Save and reopen a support interaction

Add PostgreSQL interaction/attempt persistence, repository contracts, SQLAlchemy
adapters, and a reviewed Alembic baseline. Show saved questions and drafts in the UI.
Use durable cloud PostgreSQL rather than application-container storage.

Define what is persisted when inference fails, how retries are identified, and how
duplicate submissions are handled. Do not hold a database transaction across a model
call. This interaction record is not the full Stage 3 case lifecycle.

Learning: explain provenance and failure semantics around a nondeterministic external
call. Keep familiar CRUD scaffolding concise.

Verification: disposable-PostgreSQL integration/migration tests; API save/reopen tests;
persisted result survives application task replacement; secrets are absent from records.
Deploy and demonstrate the saved interaction journey.

## Slice 1.3: Make agent behavior and operations visible

Instrument application/agent/tool spans and correlate them in Phoenix. Add Prometheus
metrics and a Grafana dashboard for requests, latency, errors, tool failures, and
available model usage/estimated cost. Keep labels bounded. Provision local Compose
services and the chosen cloud telemetry collection/storage arrangement.

Document trace content, redaction, retention, access, destinations, and export toggles.
Disable or configure additional framework exporters deliberately. Confirm which
calls and traces leave the environment. Do not allow telemetry failures to fail a
successful support interaction.

Learning: use a trace to explain a failed or ungrounded answer; distinguish tracing,
metrics, logs, and evaluation. Explain estimated cost limitations.

Verification: inspect a real correlated trace and dashboard; exercise a tool error
and unavailable collector; verify redaction and access. Deploy and demonstrate.

## Slice 1.4: Establish an evidence-based evaluation baseline

Author a small versioned set of answerable, unanswerable, ambiguous, and adversarial
questions with expected supporting evidence. Add RAGAS-based grounded-answer
assessment where appropriate, deterministic reference/schema/tool checks, and a
human review rubric. Retrieval ranking metrics wait for Stage 2.

Record prompt/model/judge configuration, source versions, outcomes, latency, and
estimated cost. Run a controlled prompt comparison. Calibrate judge output against
human review before selecting blocking quality thresholds.

Learning: explain what each metric can and cannot establish. Demonstrate one case
where a plausible answer fails grounding or a judge disagrees with human review.

Verification: repeatable budgeted evaluation command; no real model calls in default
tests; separate explicitly enabled evaluation workflow. Ship any justified prompt
improvement with baseline comparison evidence, not an arbitrary score target.

## Slice 1.5: Validate and document the complete release

Exercise provider timeout, invalid tool arguments, duplicate submission, application
restart, and telemetry outage. Confirm request/turn/token/concurrency limits and
bounded retries. Finish cost, access, data-flow, recovery, rollback, and teardown
guidance. Add a small operator-facing failure/retry improvement if testing exposes
one. Reuse previously passing checks unless changes justify rerunning them.

Learning: distinguish failure prevention, diagnosis, recovery, and cloud spending
alerts from actual application-enforced limits.

Verification: complete live ask/save/reopen journey; persisted data survives restart;
one trace and dashboard; baseline evaluation evidence; deployment smoke check and
rollback demonstration. Document remaining limitations and learning conclusions.

## Completion evidence

Record the release commit/image identity, validation results, deployment smoke result,
evaluation report location/configuration, privacy/cost decisions, and concise learning
notes. Do not commit sensitive traces or secrets. Stage 1 is complete only after its
master-plan gate is demonstrated. Plan Stage 2 slices after reviewing those results.
