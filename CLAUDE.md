# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

Chronicity is a take-home challenge for Mama Health. The deliverable is a pipeline that ingests patient interview transcripts (`data/in/interviews.json`, ~12 Crohn's disease patients) and produces structured output that answers four business questions. The expected artefacts (per `README.md`) are: the four business answers, a pipeline design write-up, an evaluation section, a churn/limitations discussion, and an AI-usage note.

The repo is intentionally early-stage: `src/` and `tests/` are empty. Most of the existing work lives in `notebooks/00_setup.ipynb`, which documents the LLM-tooling decisions and verifies the Gemini path works end-to-end. Treat that notebook as the source of truth for *why* the stack was chosen.

## Stack

- **Python 3.14** (pinned in `.python-version`), managed with **uv** (lockfile is `uv.lock`).
- **LiteLLM** is the LLM gateway; **Gemini 2.5 Flash Lite** (`gemini/gemini-2.5-flash-lite`) is the working model. Authentication is via `GEMINI_API_KEY` loaded from `.env` with `python-dotenv`.
- **Pydantic** for schemas, **pandas** for tabular work, **Dagster** and **FastAPI** are declared dependencies but not yet wired.
- Lint/type/test toolchain is deliberately Rust-based: **ruff**, **ty**, **pytest**. Prefer these over Black/mypy.

`requirements.txt` is a uv export (with hashes) kept for the reviewer's build — regenerate it after changing dependencies; don't hand-edit.

## Commands

```bash
# install / sync the venv from uv.lock
uv sync

# regenerate requirements.txt after dep changes
uv export --format requirements.txt --output-file requirements.txt

# register the venv as a Jupyter kernel named "chronicity"
uv run python -m ipykernel install --user --name chronicity --display-name "Python (chronicity)"

# run things inside the venv
uv run pytest                       # all tests
uv run pytest tests/test_foo.py::test_bar   # single test
uv run ruff check                   # lint
uv run ruff format                  # format
uv run ty check                     # type-check
```

## Architecture notes

- **LLM access pattern**: go through `litellm.completion(model="gemini/...", ...)`, not the raw `google-genai` SDK. The SDK is only present because it was used in the notebook to sanity-check the API key before LiteLLM was wired in. LiteLLM gives us `response_format={"type": "json_object"}` and a `response_schema` hook for Gemini (with optional `enforce_validation: true`) — prefer that over hand-parsing model output.
- **Reproducibility**: `gemini-2.5-flash-lite` supports reasoning (`litellm.supports_reasoning(...)` returns True) and caching/TTL. If you add prompt caching or thinking-mode toggles, document them where they're set — they affect token accounting and run-to-run determinism.
- **Data layout**: `data/in/` is committed input (`interviews.json`), `data/out/` is for generated artefacts, `data/prompts/` for prompt templates. Keep generated outputs out of `data/in/`.