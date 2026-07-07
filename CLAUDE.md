# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

Crohnicity is a health-tech take-home, now a public prototype. The deliverable is a pipeline that ingests patient interview transcripts (`data/in/interviews.json`, 50 Crohn's disease patients) and produces structured output that answers four business questions. The expected artefacts (per `docs/SOLUTION.md`, the data-generated solution write-up) are: the four business answers, a pipeline design write-up, an evaluation section, a churn/limitations discussion, and an AI-usage note. `README.md` is the high-level public overview.

Pipeline code lives in `src/`, with matching `pytest` tests in `tests/`. `notebooks/` are for prototyping and visual inspection — `00_setup.ipynb` records *why* the stack was chosen. Design notes, open questions, and the work backlog live in `docs/` (`SCHEMA.md`, `QUESTIONS.md`, `TODO.md`).

## Stack

- **Python 3.14** (pinned in `.python-version`), managed with **uv** (lockfile is `uv.lock`).
- **LiteLLM** is the LLM gateway to **Gemini**; the working model is the single source of truth in `config.json` (`config.MODEL`, which also resolves the `CROHNICITY_MODEL` env override) — don't hard-code a model name in docs. Authentication is via `GEMINI_API_KEY` loaded from `.env` with `python-dotenv`. *(Model/reasoning changes are recorded in `CHANGELOG.md`.)*
- **Pydantic** for schemas, **pandas** for tabular work, **Dagster** and **FastAPI** are declared dependencies but not yet wired.
- Lint/type/test toolchain is deliberately Rust-based: **ruff**, **ty**, **pytest**. Prefer these over Black/mypy.

`requirements.txt` is a uv export (with hashes) kept for the reviewer's build — regenerate it after changing dependencies; don't hand-edit.

## Code style

- **Write the shortest, most minimal, most concise code that does the job.** Favour the smallest change that works over a more general, clever, or defensive one. No speculative abstraction and no scaffolding for features we don't have yet.
- **Small, reviewable changes.** Keep each change and commit small and self-contained so it reads as a single diff that's easy to review — not giant PR-style batches.
- **Type checking and linting are required, not optional.** Code must pass `ruff check`, `ruff format`, and `ty check` (the Rust-based toolchain above — not Black/mypy).
- **Run `bash tests/type_lint_unit_tests.sh` on every code update** — it runs `ruff check`, `ruff format --check`, `ty check`, and `pytest`, which must all pass. Do this after each change. We deliberately do **not** use pre-commit hooks — overkill for this project; the discipline is manual and per-update. (Where validation belongs — the `litellm.completion(...)` prompt-call boundary vs. the Pydantic/pandas steps — is tracked in `docs/TODO.md`.)

## Commands

```bash
# quality gate — run on every code change (ruff check + ruff format --check + ty + pytest)
bash tests/type_lint_unit_tests.sh

# install / sync the venv from uv.lock
uv sync

# regenerate requirements.txt after dep changes
uv export --format requirements.txt --output-file requirements.txt

# register the venv as a Jupyter kernel named "crohnicity"
uv run python -m ipykernel install --user --name crohnicity --display-name "Python (crohnicity)"

# run things inside the venv
uv run pytest                       # all tests
uv run pytest tests/test_post_extraction_eda.py  # a single test file
uv run ruff check                   # lint
uv run ruff format                  # format
uv run ty check                     # type-check

# run the pipeline
uv run jupyter lab                  # extraction / EDA notebooks (current driver)
uv run python src/referral_pathway_analysis.py   # phase/transition tables + journey graphs

# serve / build the MkDocs API docs locally (site/ is gitignored)
uv run mkdocs serve                 # live preview at http://127.0.0.1:8000
uv run mkdocs build                 # render the static site to site/
```

## Architecture notes

- **LLM access pattern**: go through `litellm.completion(model="gemini/...", ...)`, not the raw `google-genai` SDK. The SDK is only present because it was used in the notebook to sanity-check the API key before LiteLLM was wired in. LiteLLM gives us `response_format={"type": "json_object"}` and a `response_schema` hook for Gemini (with optional `enforce_validation: true`) — prefer that over hand-parsing model output.
- **Reproducibility**: extraction is a classification task, so **reasoning is disabled** (`reasoning_effort="disable"` → `thinkingBudget=0`, in `extract.py`) alongside `temperature=0` — thinking is off to avoid run-to-run variance and output-budget truncation (see docs/SOLUTION.md → Determinism). Document any further caching/thinking toggles where they're set — they affect token accounting and determinism.
- **Data layout**: `data/in/` is committed input (`interviews.json`), `data/out/` is for generated artefacts, `data/prompts/` for prompt templates. Keep generated outputs out of `data/in/`.
- **Single source of truth for values.** Current values — model, paths, gold/app versions, ports, decoding params — live in `config.json` / `pyproject.toml`. **In any doc, don't restate a literal; link to its SSOT file** (and in a `.qmd`, render it dynamically, e.g. `` `{python} MODEL` ``). Record *changes* over time in `CHANGELOG.md` (pipeline) / `docs/SCHEMA.md` (schema) — naming old→new values there is correct, because that's history, not a live pointer.
- **Notebooks**: jupytext-paired (`ipynb,py:percent`). **Edit notebook code in the `.py`** (the editing source of truth → clean diffs) and run `jupytext --sync`; **never hand-edit the `.ipynb`** — that's the human's running/viewing copy, where outputs live. `notebooks/` is excluded from the gate. Full workflow: `docs/DEV_SETUP.md`.