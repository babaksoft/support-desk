# Support Desk Design

Last updated: 2026-11-11

## Purpose and scope

Support Desk helps an operator support Boardlight, a fictional team task-board
SaaS product. Its four core use cases are answering a product question,
investigating an account issue,
reviewing and resolving a case, and proposing a knowledge improvement. Supported
case categories are account access, billing questions, and technical troubleshooting.

Boardlight accounts can belong to multiple workspaces. Each workspace has its own
Free or Pro subscription; an upgrade applies to the selected workspace. The
[versioned product evidence](docs/product/boardlight/README.md) defines plan limits,
activation rules, access behavior, and basic troubleshooting.

The recurring scenario is: “My account still shows the free plan after upgrading.”
The operator uses product evidence and synthetic subscription information to
investigate, request missing details, and review an evidence-backed response.

The application drafts responses and proposals for operator review. External
message sending, real customer integrations, autonomous account changes, and
multi-channel ticket management are outside the core scope.

## Design goals and constraints

Keep the product small while deepening AI quality, observability, reliability,
and operational maturity. Familiar full-stack components support learning in AI
Engineering, LLMOps, and DevOps. Each framework has a distinct product responsibility.
Incremental features remain deployable. Infrastructure and agent complexity must
be justified by an observable behavior or measured operational need.

## System context

An operator uses Streamlit, which calls FastAPI. Application use cases access
product documentation, synthetic account information, model providers, and durable
storage through adapters. Human review controls acceptance of generated artifacts.
Telemetry and evaluation systems observe behavior; they do not own business state.

## Architecture and dependency rules

Use a modular monolith: domain values and contracts, application use cases,
infrastructure adapters, thin API/UI, and explicit composition roots. Dependencies
point inward. Persistence queries belong in repositories. Framework types do not
cross application boundaries.

OpenAI Agents SDK owns interactive assistance, tool use, and bounded specialist
handoffs. LangChain adapters own ingestion and retrieval. LangGraph owns durable
case workflows. CrewAI owns bounded support-analysis and knowledge-proposal jobs.
LangGraph may invoke such a job but retains case lifecycle ownership. Do not give
CrewAI Flows competing ownership of that lifecycle.

Add a worker using the same codebase when durable or long-running jobs require it.
Persisted checkpoints require an execution/resumption mechanism; they are not a
substitute for job scheduling or recovery supervision.

## Domain model and invariants

- A support case groups an operator's investigation, drafts, review, and resolution.
- A support interaction records a question and generated result; it can exist
  before the full case workflow is introduced.
- A knowledge source has a stable identity and version. Evidence references identify
  the source material used for a generated artifact.
- Synthetic customer/subscription records provide bounded facts for investigations.
- A response draft distinguishes evidence-backed facts, hypotheses, and missing
  information. Insufficient evidence must not become an invented account fact.
- A generation attempt records its outcome and relevant configuration/provenance.
- A review applies to a specific artifact version. Changed drafts need fresh review.
- A knowledge proposal is a draft until accepted by an operator. Generating it does
  not silently change the authoritative knowledge base.

## Behavioral design

### Answer a product question

Use applicable product evidence to draft a useful answer with source references.
When evidence is insufficient, explain the gap and request relevant information.
Reference selection starts bounded; retrieval extends the same behavior.

### Investigate an account issue

Combine documentation and authorized synthetic account tools. Request missing
identifiers or facts rather than guessing. Specialists may take over a conversation
when distinct instructions and tool access improve the investigation.

### Review and resolve a case

The intended lifecycle is intake, investigation, missing-information wait when
needed, draft, operator review, and resolution. Review can return work for revision.
State survives process restarts. Repeated commands or resumed execution must not
duplicate business writes. Approval does not authorize external sending.

### Propose a knowledge improvement

Analyze selected resolved cases using bounded analyst, documentation, and reviewer
roles. Produce a cited FAQ proposal identifying supporting cases, uncertainty, and
possible documentation gaps. Human review controls acceptance.

## Data ownership and persistence

PostgreSQL owns application records and durable workflow state. pgvector supports
retrieval when introduced. SQLAlchemy repositories own business persistence;
Alembic manages reviewed migrations. Framework checkpoints remain separate from
canonical case records, with explicit consistency and recovery contracts.

Store source/configuration provenance sufficient to investigate generated results.
Do not hold database transactions open across model calls. Define failed-attempt,
retry, and deduplication semantics before adding durable jobs. Container-local
filesystems are not durable storage for application records.

## External interfaces and integrations

FastAPI provides typed application interfaces; Streamlit is the operator client.
The three agent frameworks are infrastructure dependencies behind bounded contracts.
Cloud models may receive selected questions, evidence, and tool results. RAGAS is
the initial evaluation choice. Phoenix with OpenTelemetry/OpenInference supplies
LLM traces; Prometheus and Grafana supply operational metrics and dashboards.

Docker Compose provides local composition. GitHub Actions provides CI/CD through
repository-scoped AWS OIDC roles. Terraform manages the AWS infrastructure. The
cloud target is one Amazon ECS/Fargate service using immutable ECR images. CloudFront
provides the AWS-generated public HTTPS endpoint and reaches an internal Application
Load Balancer through a VPC origin. Cognito federates Google identities; FastAPI
enforces operator-group authorization. Private database subnets reserve the later
RDS PostgreSQL destination. Specific versions and model identifiers are verified
during implementation rather than fixed by this design.

## Cross-cutting concerns

### Quality and evaluation

Combine deterministic business/tool tests with versioned evaluation examples and
human review. Assess grounding, retrieval quality, tool selection and arguments,
abstention, review outcomes, and end-to-end task success separately. Compare
changes against a baseline; a single aggregate judge score is insufficient.

### Privacy and access

Use authored documents and synthetic customer data initially. Keep model data flow
separate from telemetry data flow. Define redaction, retention, access, and export
destinations explicitly. Operator access and account-tool authorization are enforced
by application code. Treat retrieved content as untrusted data, not instructions.
Telemetry outages must not silently alter business outcomes.

### Reliability and capacity

Bound request sizes, model turns, tool execution, deadlines, retries, and concurrency.
Model execution may partially succeed before failure; recovery must preserve known
results without assuming exactly-once execution. Distinguish transient failures from
invalid requests. Record failures sufficiently for diagnosis without exposing secrets.

### Observability and costs

Correlate API, agent, tool, retrieval, and worker activity. Keep metric labels bounded.
Record model usage and estimated cost with the pricing/configuration basis; billing
remains external ground truth. Local telemetry does not make cloud inference local.
Cloud compute, storage, networking, evaluations, and inference need explicit budgets.

### Deployment and recovery

Provide health/readiness checks, durable persistence, secret management, controlled
schema upgrades, smoke verification, rollback, and teardown guidance. Define how
telemetry is collected and retained in cloud environments before live release.

## Related documents

- [Master plan](PLAN.md)
- [Repository conventions](AGENTS.md)
- [Product overview](README.md)
- [Stage 1 plan](docs/plans/stage-01.md)
- [Boardlight product evidence](docs/product/boardlight/README.md)
- [Decision index](docs/decisions/README.md)
