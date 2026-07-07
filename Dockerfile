# Crohnicity extraction API — local hosting (see docs/TODO.md "Next up — FastAPI service + Docker").
#
#   docker build -t crohnicity-api .
#   docker run --rm --env-file .env -p 8100:8100 crohnicity-api   # port: config.json -> api_port
#
# GEMINI_API_KEY is injected at RUNTIME via --env-file; it is never baked into the image
# (and .dockerignore excludes .env from the build context as belt-and-braces).
FROM python:3.14-slim

# uv from the official distroless image — pinned tooling without a curl|sh step.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /crohnicity
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1

# Dependencies first: this layer only rebuilds when the lock changes, not on every code edit.
# KISS note: this installs the full locked environment (incl. batch-pipeline deps the API doesn't
# use); a dedicated slim dependency group is a possible follow-up, not worth the split yet.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Only what the service needs: the app, the library it wraps, and their config/prompt inputs.
COPY config.json ./
COPY data/prompts/ data/prompts/
COPY src/ src/
COPY app/ app/

EXPOSE 8100
# Liveness via the /health endpoint; the port is read from config.json (api_port) — the SSOT.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD ["uv", "run", "--no-sync", "python", "-c", "import json,urllib.request;p=json.load(open('config.json'))['api_port'];urllib.request.urlopen(f'http://127.0.0.1:{p}/health',timeout=3)"]

# app/main.py serves on 0.0.0.0:api_port (config.json) — same SSOT as the local run.
CMD ["uv", "run", "--no-sync", "python", "app/main.py"]
