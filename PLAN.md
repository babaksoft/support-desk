# Support Desk Master Plan

## Working agreement and status

The product scope and six-stage progression are agreed. Repository preparation is
done: the initial commit is pushed and `origin` points to the GitHub repository
of the same name. The Stage 1 plan is reviewed and approved, subject to further
review questions. Its work is divided into smaller review units below. Slice 1.1
is done: local API implementation, formatting, deterministic checks, container
smoke, and bounded live inference are verified. The paid smoke recorded one safe
but semantically imperfect citation result for the later evaluation baseline.
Slice 1.2 is done: deterministic UI/API checks, the local Compose journey, and
browser review are verified. Slice 1.3 deployment decisions and the account budget
checkpoint are complete; infrastructure implementation has not started. Preparation
A is done; the user reports all GitHub CI checks passed. Preparation B is done:
Boardlight's initial reference pack and example questions are authored and checked.
Plan implementation one stage at a time and update status only with verification
evidence.

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

## Prerequisites and open choices

- Repository preparation, remote configuration, and Stage 1 plan review are done.
- OpenAI credits and an active AWS account with Bedrock model quotas are available.
  OpenAI's Python SDK and Bedrock Converse are the intended provider interfaces;
  verify model-specific capabilities before using either in an adapter. Start with
  one provider path; add another when a comparison justifies it.
- Python 3.12 meets the checked OpenAI SDK Python requirements. Recheck compatibility
  and APIs when adding runtime dependencies in the API slice.
- Boardlight, a fictional team task-board SaaS, is selected. The
  [initial reference pack](docs/product/boardlight/README.md) and example questions
  establish the product evidence for Slice 1.1.
- Choose a cheaper capable initial model and explicit smoke-run/evaluation budgets
  before networked runs. Available credits and quotas do not set spending limits.
- Slice 1.3 targets a dedicated project account in `us-east-1` using Terraform,
  GitHub OIDC, Cognito with Google, and a default CloudFront HTTPS endpoint. The
  temporary deployment experiment has a USD 10 budget with alerts. Deployment still
  requires explicit live-execution approval after reviewable infrastructure exists.
- Decide local/cloud trace destinations, export policy, retention, redaction, and
  durable telemetry storage before the first live release. Set framework exporter
  behavior before the first model run. Do not assume Compose volumes map directly
  to cloud persistence.

Resolve choices when they affect the active slice; independent local work can proceed.

## Optional future roadmap

External ticketing integrations, outbound responses, real customer data, additional
channels, autonomous actions, multilingual support, and larger-scale operations
remain optional. Adding any requires identifying the core use case improved, the
learning value, and the evidence that would justify the added complexity.
