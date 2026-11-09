# Repository Guidelines

## Purpose and execution

Support Desk is a small Python application for learning AI Engineering, LLMOps,
and DevOps. Familiar full-stack infrastructure supports that goal. Keep the core
product to the four use cases in DESIGN.md; record extensions separately in
PLAN.md. Explain consequential AI and operational choices alongside reviewable
changes. Do not generate a large implementation ahead of the active stage.

Plan detailed execution one stage at a time. Every feature slice must produce a
usable improvement, appropriate verification, and a deployable increment. Separate
repository preparation from claims of a shipped product. Do not mark delivery
complete without evidence. A cloud deployment or paid experiment must have an
agreed destination and budget before execution; normal local development proceeds
within the authorized task.

## Architecture and target structure

Use a modular monolith with dependencies pointing inward. The target package is
src/support_desk/, containing domain/, application/, infrastructure/, api/, ui/,
and composition/. Create modules when they have a concrete responsibility; do not
prebuild empty framework hierarchies.

- Domain owns business values, invariants, repository protocols, and external
  capability contracts. It imports no agent, web, or persistence framework.
- Application owns use cases, authorization decisions, and transaction boundaries.
  It depends on domain contracts, not concrete adapters.
- Infrastructure owns SQLAlchemy models, repository implementations, provider and
  agent adapters, retrieval, framework workflows, and telemetry integration.
- API and UI remain thin. Streamlit calls FastAPI rather than repositories.
- Composition constructs concrete dependencies. Framework objects stay behind
  adapters; application boundaries exchange typed requests and results.
- Persistence queries belong in repositories. Do not issue direct SQLAlchemy
  queries in services, routes, or UI code.
- Generic shared utilities must not become a home for business rules.

OpenAI Agents SDK owns interactive assistance and bounded delegation. LangChain
owns retrieval adapters. LangGraph owns durable case workflows. CrewAI owns bounded
support-analysis and FAQ-proposal jobs. Do not introduce competing workflow owners
or a universal abstraction over every framework. Add architecture checks when
these boundaries become executable.

## Dependencies and database changes

Python 3.12 is the initial baseline, subject to checking the required SDKs before
locking dependencies. Use uv and a committed uv.lock. Use uv add/uv remove with
appropriate dependency groups; do not use pip or hand-edit the lockfile. Add runtime
dependencies when the active slice needs them. Verify current official SDK APIs
before implementation.

Use PostgreSQL, SQLAlchemy, and Alembic. Add pgvector with retrieval. Review each
generated migration and test upgrade paths against a disposable PostgreSQL
database. Never edit an applied migration. Match authored-field validation limits
to sensible bounded string columns, preferably multiples of 16. Give every mapped
column and relationship a concise doc description. Prefix database repository
implementations with Db; leave domain protocol names unprefixed.

## Style

- Four-space indentation; complete type hints on every function.
- Complete Google-style docstrings on classes, methods, and functions, with a
  single blank line after the docstring.
- Use the same section formatting and description style in class and function
  docstrings. In Attributes, Args, and Raises, put each item name on its own line
  and indent its description. Omit Args without arguments and Returns for
  None-returning functions.
- Absolute package imports. Export principal architecture symbols at their owning
  package boundary and import them there except within that package.
- snake_case modules/functions; PascalCase classes; test_<behavior>.py modules and
  test_<expected_behavior> test functions.
- Use common AI terminology in class, function, and method names when precise.
- Keep technical language precise; use jargon sparingly in docstrings and living
  Markdown documents.
- Keep living Markdown documents focused and concise while preserving essential
  details.
- Describe what a class, function, or method does in its docstring. Avoid extra
  context about what it is not or does not do, such as "performs X without doing
  Y" or "never does Z."
- Pydantic domain values and application schemas; freeze immutable values. Every
  Pydantic model has an Attributes section and descriptions for every field.
- Prefer module-scope definitions over functions or classes nested inside functions
  or methods. Use nested definitions only when a required closure or framework constraint
  makes a module-scope definition impractical.
- Prefer internal helpers at the bottom; use future annotations when needed.
- Keep code and explanations purpose-specific. Avoid speculative abstractions.

## Quality and testing

Establish Black, isort, Ruff, mypy, and pytest in the first implementation slice.
The intended checks, once configured, are:

```bash
timeout 30s uv run black --check src tests
uv run isort --check-only src tests
uv run ruff check src tests
uv run mypy src tests
uv run pytest -v
```

Cap every Black invocation at 30 seconds. After a timeout, do not retry; continue
other checks independently and report Black as incomplete. Fix formatting failures
returned within the limit and rerun once with the same cap. Ensure CI runs the
remaining checks even if formatting fails or times out. Do not invoke an uncapped
Black wrapper.

Use focused unit tests, disposable-PostgreSQL integration and migration tests,
API contract tests, architecture checks, and deployment smoke tests as applicable.
Default tests must not need real credentials or unstated local services. CI starts
required integration services explicitly. Mark networked and billable model tests
separately and require explicit enablement. Use shared fixtures and fake agents
for deterministic tests. Do not substitute model-judge scores for correctness tests.

Version evaluation inputs, expected evidence, prompts, and run configuration.
Record judge/model versions, estimated cost, and limitations. Calibrate judge
scores against human review before making them blocking release gates. Keep fast
CI checks distinct from budgeted model evaluations and larger experiments.

## Documentation

README.md describes shipped capabilities and verified onboarding. Keep its eventual
organization: introduction, capabilities, scope, data behavior, architecture,
materially used technology, quick start, configuration, database management,
development checks, documentation map, license. Do not claim planned features as
available, invent setup commands, or present source constants as configurable.
Label optional, destructive, networked, billable, and data-sharing actions. Keep
one canonical setup path and relative document links. Do not add a table of
contents without a request.

DESIGN.md describes accepted intended behavior, not delivery status. Preserve its
ten top-level sections and order. Update it for durable changes in domain rules,
workflows, ownership, integrations, privacy, recovery, or architecture. Reconcile
accepted ADRs, replace superseded statements, and update Last updated for material
changes. Keep stage progress, method signatures, and setup commands elsewhere.

PLAN.md tracks outcomes, dependencies, learning objectives, release gates, status,
and the optional roadmap. Only the active stage gets a detailed plan under
docs/plans/. ADRs under docs/decisions/ state a concise decision and rationale;
execution detail belongs in stage plans. Learning records capture a hypothesis,
comparison, evidence, and conclusion; do not duplicate source walkthroughs there.

After documentation edits, run git diff --check and verify relative links.
Documentation-only changes do not require the code suite.

## Operations and contributions

Use synthetic data initially. Do not commit credentials, real customer data,
telemetry exports, or local environment files. Keep telemetry redaction, retention,
and export destinations explicit. Avoid request IDs or customer identifiers as
metric labels. Enforce application authorization and tool permissions outside LLM
instructions; guardrails are an additional check, not an authorization boundary.

GitHub Actions must cover pull requests as well as the `master` branch. Use GitHub
OIDC for AWS deployment, immutable image identities, health checks, a smoke test,
and a documented rollback. Specify durable cloud storage separately from local
Compose volumes. Include teardown and budget guidance before cloud execution.

Use short imperative commit subjects and cohesive commits. PRs explain behavior,
validation, migrations/config changes, operational steps, and relevant issues;
include screenshots for UI changes. Do not publish, create a remote repository, or
perform a live deployment unless requested. Review explanations should emphasize
AI engineering and operational tradeoffs; expand code explanations when requested.
