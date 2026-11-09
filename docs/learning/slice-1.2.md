# Typed UI-to-API boundary

Hypothesis: keeping Streamlit behind a typed HTTP client preserves the FastAPI
application boundary while still giving operators useful distinctions between a
generation failure, an unavailable API, and an invalid response.

Comparison: client tests exercise a valid typed draft, the API's declared safe
failure, a transport failure, and malformed success/failure payloads. Streamlit's
headless AppTest submits an authored Boardlight question, displays its unreviewed
draft and `BL-PLANS` evidence, rejects whitespace locally, and displays safe busy
guidance. The UI imports no repository, agent, or evidence adapter.

Evidence: `tests/ui/test_client.py`, `tests/ui/test_app.py`, and
`tests/composition/test_ui.py` cover the new boundary. The complete 55-test suite,
isort, Ruff, strict mypy, lock consistency, Compose configuration, package builds,
and `git diff --check` passed on 2026-11-09. The capped Black check later completed
with all 50 files unchanged. The two-service Compose build and health checks passed,
and browser review covered the form, an answered draft with `BL-PLANS` v1 evidence,
and the safe inference-disabled failure. Detailed evidence and screenshots are in
the [Stage 1 report](../plans/stage-01-report.md#slice-12).

Conclusion: the UI can remain a replaceable operator client when it exchanges the
same validated request and domain result as other API consumers. Headless component
tests efficiently establish form behavior and boundary mapping, while the Compose
and browser checks establish packaging, startup ordering, service connectivity, and
operator-visible behavior. A deterministic adapter is sufficient for successful UI
rendering checks; live inference compatibility and quality remain separate, budgeted
evidence from Slice 1.1. No additional model cost was needed for this slice.
