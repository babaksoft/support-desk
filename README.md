# Support Desk

Support Desk is a Python learning project for building and operating a small,
evidence-based support application for one fictional SaaS product. Its primary
learning focus is AI Engineering, LLMOps, and DevOps.

The local FastAPI increment drafts product guidance through an OpenAI Agents SDK
reference-lookup tool and returns an unreviewed answer with versioned evidence or
an explicit evidence gap. Deterministic tests exercise the API and real SDK loop
with synthetic provider responses. Live model behavior awaits a budgeted smoke run;
there is no configured cloud deployment.

## Capabilities

- `POST /questions`: bounded question generation with structured drafts and citations.
- `GET /health/live`: process liveness; `GET /health/ready`: local configuration readiness.
- Packaged Boardlight v1 evidence, also included in the wheel and container.

## Product scope

The fictional supported product is Boardlight, a team task-board SaaS with Free and
Pro workspace subscriptions. The [initial reference pack](docs/product/boardlight/README.md)
defines its authored product rules and example questions.

Support Desk has four intended use cases: answer a product question,
investigate an account issue, review and resolve a case, and propose a knowledge
improvement. Support responses and knowledge proposals require operator review.
This increment covers general product guidance using authored documentation.
Account tools, Streamlit, persistence, and case workflows remain planned.

## Data and cloud usage

Model inference and model-based evaluations may transmit selected inputs to cloud
providers and incur charges. AWS deployment incurs infrastructure charges.
SDK tracing is disabled per run, including sensitive trace content. No telemetry
exporter or application record storage is configured. The OpenAI Responses request
sets `store=False`; this does not establish provider-side zero retention. Inference
sends the question, instructions, output schema, and selected evidence to OpenAI.
Use authored questions only. Local telemetry does not imply local inference.

## Architecture overview

The intended architecture is a modular monolith with domain values, application
use cases, and infrastructure adapters. FastAPI serves the application boundary;
Streamlit is the planned operator interface. Framework responsibilities and the
planned production stack are recorded in [DESIGN.md](DESIGN.md).

## Technology

FastAPI, Pydantic, Uvicorn, OpenAI Agents SDK, and the OpenAI client implement the
current API. Python 3.12 and uv manage the package and locked dependencies. Black and isort
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

## Run the local API

After the locked install above:

```bash
uv run uvicorn support_desk.composition.api:build_app --factory --host 127.0.0.1 --port 8000 --workers 1 --limit-concurrency 8 --no-access-log
```

Open `http://127.0.0.1:8000/docs` for the contract. In the default configuration,
liveness succeeds and readiness/question generation return 503. Readiness checks
configuration only; it does not contact OpenAI or verify model access.

## Configuration

| Environment variable | Behavior |
| --- | --- |
| `SUPPORT_DESK_ENABLE_INFERENCE` | Set exactly `1` to permit paid generation; disabled by default |
| `SUPPORT_DESK_MODEL` | Explicit OpenAI Responses model ID; no default |
| `OPENAI_API_KEY` | Provider credential, required when enabling inference |

Do not enable inference until a model and run budget are agreed. Export credentials
through your shell's secret mechanism; keep them out of source and command history.
After approval, set the variables and restart the same API command. A request is:

```bash
curl --fail-with-body http://127.0.0.1:8000/questions -H 'Content-Type: application/json' -d '{"question":"How many boards can a Free workspace have?"}'
```

**Networked, billable, data-sharing:** each accepted request when enabled may make
up to three model calls. Limits are source constants: 2,048 question characters,
16 KiB HTTP body, one active generation per process, 45-second overall deadline,
40-second provider timeout, two lookup calls (up to four sources each), and 1,024
output tokens per model turn (up to 3,072 total). Provider retries are disabled;
failures require explicit retry. These bound a request, not cumulative spending.
Cancellation cannot guarantee that remote inference stops or incurs no charge.
HTTP 429 means busy, 502 means generation failed, and 504 means deadline exceeded.

Use one worker and localhost: the admission slot is process-local, and this increment
has no operator authentication. Shared hosting/access controls arrive in Slice 1.3.

## Container

**Networked build:** downloads base images and locked dependencies.

```bash
docker build -t support-desk:slice-1.1 .
docker run --rm -p 127.0.0.1:8000:8000 support-desk:slice-1.1
```

The container runs as a non-root user, starts one worker, and checks liveness.
It starts with inference disabled. No database or volume is needed. Remove the
local image with `docker image rm support-desk:slice-1.1` when finished.

## Database management

This increment stores no interactions. PostgreSQL and migrations arrive in Slice 1.4.

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
