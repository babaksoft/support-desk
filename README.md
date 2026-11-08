# Support Desk

Support Desk is a Python learning project for building and operating a small,
evidence-based support application for one fictional SaaS product. Its primary
learning focus is AI Engineering, LLMOps, and DevOps.

This repository contains the design, delivery plans, and an installable Python
package with development checks and CI configuration. There is no runnable
application or configured cloud deployment yet.

## Product scope

The fictional supported product is Boardlight, a team task-board SaaS with Free and
Pro workspace subscriptions. The [initial reference pack](docs/product/boardlight/README.md)
defines its authored product rules and example questions.

Support Desk has four intended use cases: answer a product question,
investigate an account issue, review and resolve a case, and propose a knowledge
improvement. Support responses and knowledge proposals require operator review.
Initial data consists of authored documentation and synthetic customer records.

## Data and cloud usage

Model inference and model-based evaluations may transmit selected inputs to cloud
providers and incur charges. AWS deployment incurs infrastructure charges.
Telemetry destinations, redaction, retention, and access controls will be chosen
before the first live release. Local telemetry does not imply local inference.

## Architecture overview

The intended architecture is a modular monolith with domain values, application
use cases, and infrastructure adapters. FastAPI serves the application boundary;
Streamlit provides the operator interface. Framework responsibilities and the
planned production stack are recorded in [DESIGN.md](DESIGN.md).

## Development technology

Python 3.12 and uv manage the package and locked dependencies. Black and isort
format code; Ruff checks lint, annotations, and Google-style docstrings; mypy checks
types in strict mode; pytest runs deterministic tests. GitHub Actions configures
independent checks for pull requests and pushes to `master`.

## Quick start

From the repository root, use Python 3.12 and uv 0.12.7 (the CI version).
See the official [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/)
if needed. Dependency installation is networked and downloads packages from PyPI;
uv may also download Python if 3.12 is unavailable locally.

```bash
uv sync --locked
```

This creates `.venv` and installs the project and development tools from `uv.lock`.
Subsequent `uv run` commands use that environment automatically. The current checks
require no model credentials, database, or cloud services.

## Development checks

Run each check independently from the repository root:

```bash
timeout 30s uv run black --check src tests
uv run isort --check-only src tests
uv run ruff check src tests
uv run mypy src tests
uv run pytest -v
```

`timeout` requires GNU coreutils. If Black times out, record it as incomplete,
continue the other checks, and do not retry it. CI runs checks as separate jobs
with fail-fast disabled. Build the source distribution and wheel with `uv build`;
generated files go into the ignored `dist/` directory.

See the [Stage 1 plan](docs/plans/stage-01.md) for verification evidence and pending
checks.

## Documentation map

- [AGENTS.md](AGENTS.md): repository conventions and quality requirements.
- [DESIGN.md](DESIGN.md): intended behavior and architecture.
- [PLAN.md](PLAN.md): delivery stages and completion criteria.
- [Stage 1](docs/plans/stage-01.md): walking-skeleton slices.
- [Boardlight](docs/product/boardlight/README.md): product evidence and example questions.
- [Decisions](docs/decisions/README.md): concise architectural decisions.
- [Learning record](docs/learning/README.md): measured experiments and lessons.

## License

Licensed under the [MIT License](LICENSE).
