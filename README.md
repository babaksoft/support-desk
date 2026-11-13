# Support Desk

Support Desk is a Python learning project for building and operating a small,
evidence-based support application for one fictional SaaS product. Its primary
learning focus is AI Engineering, LLMOps, and DevOps.

The local Streamlit interface sends product questions to FastAPI, which drafts
guidance through an OpenAI Agents SDK reference-lookup tool. It displays an
unreviewed answer with versioned evidence or an explicit evidence gap. Deterministic
tests exercise the UI, API, and real SDK loop with synthetic provider responses. A
bounded paid smoke verified live inference, including one recorded semantic citation
limitation. There is no configured cloud deployment.

## Capabilities

- `POST /questions`: bounded question generation with structured drafts and citations.
- `GET /health/live`: process liveness; `GET /health/ready`: local configuration readiness.
- Streamlit question form with draft, evidence, and safe failure displays.
- Application-enforced operator authorization with local and Cognito adapters.
- Packaged Boardlight v1 evidence, also included in the wheel and container.

## Product scope

The fictional supported product is Boardlight, a team task-board SaaS with Free and
Pro workspace subscriptions. The [initial reference pack](docs/product/boardlight/README.md)
defines its authored product rules and example questions.

Support Desk has four intended use cases: answer a product question,
investigate an account issue, review and resolve a case, and propose a knowledge
improvement. Support responses and knowledge proposals require operator review.
This increment covers general product guidance using authored documentation.
Account tools, persistence, and case workflows remain planned.

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
the Streamlit operator interface calls it through a typed HTTP client. Framework
responsibilities and the planned production stack are recorded in [DESIGN.md](DESIGN.md).

## Technology

Streamlit and HTTPX implement the operator client. FastAPI, Starlette, Pydantic,
PyJWT, Uvicorn, OpenAI Agents SDK, and the OpenAI client implement the current API.
Starlette supplies ASGI types and response primitives for the bounded request
middleware. Python 3.12 and uv manage the package and locked dependencies. Black
and isort format code; Ruff checks lint, annotations, and Google-style docstrings;
mypy checks types in strict mode; pytest, pytest-asyncio, and Streamlit AppTest run
deterministic tests. GitHub Actions configures independent checks for pull requests
and pushes to `master`.

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
generation and authentication configuration only; it does not contact OpenAI,
Cognito, or verify external access.

In another terminal, start the operator interface:

```bash
uv run streamlit run src/support_desk/composition/ui.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. The default API remains inference-disabled, so a
submitted question shows the safe configuration failure until inference is
explicitly enabled.

## Configuration

| Environment variable | Behavior |
| --- | --- |
| `SUPPORT_DESK_AUTH_MODE` | `local` for loopback development or `cognito` for deployed token verification; defaults to `local` |
| `SUPPORT_DESK_COGNITO_ISSUER` | Exact HTTPS Cognito user-pool issuer; required in `cognito` mode |
| `SUPPORT_DESK_COGNITO_CLIENT_ID` | Cognito app client accepted by the API; required in `cognito` mode |
| `SUPPORT_DESK_UI_AUTH_MODE` | `local` for the loopback UI or `cognito` for Streamlit OIDC login; defaults to `local` |
| `SUPPORT_DESK_COGNITO_CLIENT_SECRET` | Confidential Cognito client secret supplied to the deployed UI from Secrets Manager |
| `SUPPORT_DESK_SESSION_COOKIE_SECRET` | Streamlit identity-cookie signing secret supplied from Secrets Manager |
| `SUPPORT_DESK_PUBLIC_URL` | Public deployed UI root used to construct the exact `/oauth2callback` URI |
| `SUPPORT_DESK_OPERATOR_GROUP` | Cognito group authorized for operator use cases; defaults to `operators` |
| `SUPPORT_DESK_ENABLE_INFERENCE` | Set exactly `1` to permit paid generation; unset or `0` disables it |
| `SUPPORT_DESK_MODEL` | Explicit OpenAI Responses model ID; no default |
| `OPENAI_API_KEY` | Provider credential, required when enabling inference |
| `SUPPORT_DESK_API_URL` | Streamlit API root; defaults to `http://127.0.0.1:8000` |

`local` authentication creates a synthetic operator and is allowed only for the
documented loopback and local Compose paths. A shared deployment must use `cognito`;
the API then verifies the RS256 signature, expiry, issuer, app client, access-token
use, and group claims before the application authorizes the `operators` group.
Health endpoints remain public. Reviewable Terraform and a protected manual delivery
workflow define the Cognito and application infrastructure, immutable image delivery,
rollback, stop, and teardown. The temporary Slice 1.3 platform completed its live
Google-federated operator journey, rollback demonstration, and confirmed teardown.
The application resources and release images are no longer deployed; encrypted remote
state and restricted GitHub OIDC bootstrap roles remain for later slices. Streamlit
clears its application session on sign-out, but provider-level Cognito/Google single
sign-out remains a documented interoperability limitation.

Do not enable inference until a model and run budget are agreed. Export credentials
through your shell's secret mechanism; keep them out of source and command history.
After approval, set the variables and restart the same API command. Invalid enablement
values and enabled inference without both other settings fail during process startup.
A local-mode request is:

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
API failures contain stable `code` and safe `message` fields. HTTP 401 means the
access token is invalid, 403 means the actor lacks operator access, 413 means the
request is too large, 429 means busy, 502 means generation failed, 503 means a
dependency is unavailable, and 504 means the deadline was exceeded.

### Paid model smoke

**Networked, billable, data-sharing:** the Slice 1.1 smoke sends two authored
questions and selected Boardlight evidence to OpenAI. It uses the pinned
`gpt-5.4-mini-2026-03-17` snapshot, disables SDK tracing and provider storage,
permits at most six model calls and 6,144 output tokens, and has no automatic
retries. The completed follow-up experiment budget was USD 0.10.

Create the ignored, mode-`600` `.env.smoke` file outside Codex output with the three
configuration variables above. Do not add automatic dotenv loading to application
startup. Run the fixed experiment explicitly:

```bash
uv run --env-file .env.smoke python -m support_desk.composition.model_smoke
```

The command emits sanitized JSON Lines containing each completed case before its
postconditions, followed by the aggregate report. Records include drafts,
tool/source behavior, response IDs, token usage, latency, and estimated standard
token cost. It never emits the credential. Each execution is a new paid experiment
and requires an agreed budget.

The recorded follow-up used four model calls, 3,959 input tokens, and 243 output
tokens, with estimated standard token cost USD 0.00406275. Board capacity passed
the authored evidence expectation. Refund policy safely returned insufficient
evidence but cited the plan and upgrade sources it inspected; those citations do
not prove that no separate refund policy exists. This limitation is retained for
the evaluation baseline.

Use one worker and localhost: the admission slot is process-local. The local
authentication adapter is not a shared-hosting access control; deployed Cognito
configuration and login arrive with the Slice 1.3 infrastructure.

## Local Compose

**Networked build:** downloads base images and locked dependencies.

```bash
SUPPORT_DESK_ENABLE_INFERENCE=0 SUPPORT_DESK_MODEL= OPENAI_API_KEY= docker compose --env-file /dev/null up --build
```

Compose starts the non-root API on `127.0.0.1:8000`, waits for its liveness check,
and then starts Streamlit on `127.0.0.1:8501`. Both services have health checks.
This command explicitly disables inference and ignores local dotenv files. No
database or volume is needed. Stop the services with `docker compose down`.

**Networked, billable, data-sharing:** after agreeing a new run budget, the same
stack can load the ignored mode-`600` smoke settings explicitly with
`docker compose --env-file .env.smoke up --build`. Each submitted question is a
new paid attempt under the limits described above.

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
- [Application platform](infra/platform/README.md): review and safety boundary for
  the stopped Slice 1.3 AWS stack and delivery operations.
- [Boardlight](docs/product/boardlight/README.md): product evidence and example questions.
- [Decisions](docs/decisions/README.md): concise architectural decisions.
- [Learning record](docs/learning/README.md): measured experiments and lessons.

## License

Licensed under the [MIT License](LICENSE).
