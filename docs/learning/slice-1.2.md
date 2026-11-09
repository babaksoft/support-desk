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
and `git diff --check` passed on 2026-11-09. Local Uvicorn and Streamlit processes
reported healthy on ports 8000 and 8501. An authored question reached the
inference-disabled API and returned its declared `generation_unavailable` response.

Conclusion: the UI can remain a replaceable operator client when it exchanges the
same validated request and domain result as other API consumers. Headless component
tests establish form behavior and boundary mapping without model spend. They do not
replace a browser screenshot or prove container build reproducibility.

Operational limitation: Compose validation passed, but the local image build could
not resolve `python:3.12-slim` because Docker Hub returned HTTP 403 before project
code ran. No browser capture tool was available, so the Compose runtime smoke and
review screenshot remain required before Slice 1.2 is marked complete. No model
call was made and no additional cost was incurred.
