# Support Desk Master Plan

## Working agreement and status

The product scope and six-stage progression are agreed. This document and the
Stage 1 slice plan are initial drafts for review. Repository preparation is in
progress; no application feature or deployment is complete. Plan implementation
one stage at a time and update status only with verification evidence.

Primary learning: AI Engineering foundations, agent frameworks, evaluation,
observability, LLMOps, and DevOps. Full-stack infrastructure is supporting work.

## Core use cases

| Use case | Intended outcome |
| --- | --- |
| Answer a product question | Grounded draft with evidence or explicit insufficient evidence |
| Investigate an account issue | Combine documentation and synthetic account facts |
| Review and resolve a case | Operator-controlled revision, review, and durable continuation |
| Propose a knowledge improvement | Evidence-backed FAQ proposal from selected resolved cases |

Use the upgraded-account-still-on-free-plan scenario throughout. Product completion
means these four use cases meet the agreed quality and operational gates. Additional
experimentation does not automatically expand the completion criteria.

## Stage 1: Ship the walking skeleton

Outcome: an operator asks a product question, receives a draft based on a fixed
reference pack, saves it, and reopens it in a live deployment.

Learn: a real Agents SDK tool loop, typed boundaries, baseline evaluations, trace
interpretation, metrics, and the complete deployment path. Establish familiar
infrastructure with minimal ceremony. Ship real model inference and durable
PostgreSQL persistence; fake agents are for deterministic tests.

Gate: working FastAPI/Streamlit journey on ECS/Fargate; one bounded tool; persisted
results survive task replacement; versioned evaluation baseline; a Phoenix trace;
a useful Grafana dashboard; access control, bounded requests/calls, secrets, smoke
test, rollback, teardown, and documented data flow/cost choices.

Detailed plan: [Stage 1](docs/plans/stage-01.md).

## Stage 2: Improve answers with versioned retrieval

Outcome: answers search a larger versioned product knowledge collection and show
citations. Introduce LangChain retrieval and pgvector.

Learn: ingestion, chunking, embeddings, retrieval diagnostics, evidence provenance,
and RAGAS retrieval/grounding evaluations. Compare against the fixed-pack baseline.

Gate: valid source references; version-aware evidence; unanswerable-question tests;
measured retrieval/answer results and latency/cost tradeoffs. Define dataset-specific
acceptance criteria during stage planning rather than inventing universal scores.

## Stage 3: Add durable review and case continuation

Outcome: create, reopen, revise, review, and resolve a case across visits/restarts.
Introduce LangGraph as lifecycle owner.

Learn: explicit state transitions, human review interrupts, checkpointing, replay,
idempotency, transaction boundaries, and execution recovery.

Gate: demonstrated restart/resume; review tied to artifact version; no duplicated
business writes on repeated commands; integration tests and observable stalled work.

## Stage 4: Investigate synthetic account issues with specialists

Outcome: specialist conversations use authorized account/subscription facts to
investigate the recurring scenario and request missing information.

Learn: Agents SDK handoffs, tool contracts and permissions, guardrails, injection
resistance, failure handling, and agent/tool evaluation.

Gate: measured task success against authored scenarios; correct tool arguments;
invalid/unauthorized calls rejected in code; no invented account facts; bounded cost.

## Stage 5: Propose knowledge improvements with a crew

Outcome: selected resolved cases produce an operator-reviewed FAQ proposal.
Introduce a bounded CrewAI analyst/documentation/reviewer job.

Learn: role/task decomposition, dependent tasks, structured artifacts, cross-framework
tracing, job execution, and evaluating collaboration against a simpler baseline.

Gate: traceable supporting cases; no automatic knowledge publication; explicit
job failure/retry handling; measured quality and cost versus a single-agent baseline.

## Stage 6: Improve measured operational weaknesses

Outcome: improve selected core-use-case failures or inefficiencies discovered in
previous stages. Reliability basics remain required in earlier releases.

Learn: failure injection, load/concurrency behavior, alerting, sampled evaluation,
performance/cost tuning, and operational recovery.

Gate: agreed end-to-end scenarios pass; budgets and service targets are justified
by evidence; recovery and rollback demonstrated; core scope complete. Select the
specific improvements from measured results when planning this stage.

## Release and learning discipline

Every feature slice identifies an observable improvement, its main learning concept,
a hypothesis, validation, a live demonstration, and a short learning conclusion.
A stage can deepen an existing use case without adding a new one. Introduce a new
framework when its product responsibility becomes necessary, not merely to import it.

Keep changes small enough to explain. Offer focused explanations of consequential
classes/functions/blocks; expand on request. Record durable conclusions rather than
large transcripts. Version evaluation examples, evidence, prompts, model/judge
configuration, results, and cost estimates. Human-review early judge scores.

Use deterministic tests in normal CI and explicitly enabled, budgeted networked
evaluations. Establish release thresholds from baselines and human calibration.
Changes ship with applicable integration checks, documentation, and recovery guidance.

## Open choices before implementation or deployment

- Confirm the initial drafts and Python/SDK compatibility before locking dependencies.
- Choose the fictional SaaS product and author the first small reference pack.
- Choose initial model access and evaluation budget before networked runs.
- Choose the GitHub remote/visibility and fill in the MIT copyright holder before
  publishing.
- Choose AWS account/region, infrastructure tool, access mechanism, and budget before
  provisioning. Deployment itself requires an explicit execution request.
- Decide local/cloud trace destinations, export policy, retention, redaction, and
  durable telemetry storage before the first live release. Do not assume Compose
  volumes map directly to cloud persistence.

Resolve choices when they affect the active slice; independent local work can proceed.

## Optional future roadmap

External ticketing integrations, outbound responses, real customer data, additional
channels, autonomous actions, multilingual support, and larger-scale operations
remain optional. Adding any requires identifying the core use case improved, the
learning value, and the evidence that would justify the added complexity.
