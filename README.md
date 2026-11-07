# Support Desk

Support Desk is a Python learning project for building and operating a small,
evidence-based support application for one fictional SaaS product. Its primary
learning focus is AI Engineering, LLMOps, and DevOps.

This repository currently contains the initial design and delivery plans. There
is no runnable application or configured cloud deployment yet.

## Product scope

The intended product supports four use cases: answer a product question,
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

## Getting started

Start with the [master plan](PLAN.md) and the
[Stage 1 plan](docs/plans/stage-01.md). Installation, configuration, database,
deployment, and development-check commands will be documented when they exist
and have been verified.

## Documentation map

- [AGENTS.md](AGENTS.md): repository conventions and quality requirements.
- [DESIGN.md](DESIGN.md): intended behavior and architecture.
- [PLAN.md](PLAN.md): delivery stages and completion criteria.
- [Stage 1](docs/plans/stage-01.md): walking-skeleton slices.
- [Decisions](docs/decisions/README.md): concise architectural decisions.
- [Learning record](docs/learning/README.md): measured experiments and lessons.

## License

Licensed under the [MIT License](LICENSE).
