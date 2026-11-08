FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src

RUN uv sync --locked --no-dev && useradd --uid 10001 --create-home app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD ["/app/.venv/bin/python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

CMD ["/app/.venv/bin/uvicorn", "support_desk.composition.api:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "8", "--timeout-keep-alive", "5", "--no-access-log"]
