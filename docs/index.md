# Crohnicity — developer docs

**Crohnicity** (Crohn's + chronicity) is a take-home pipeline that extracts structured labels from
50 Crohn's-disease patient interviews — via LiteLLM + Gemini, validated with Pydantic — to answer
four business questions.

This is the **developer docsite**: an auto-generated API reference (rendered from docstrings by
[mkdocstrings](https://mkdocstrings.github.io/), **rebuilt on every `mkdocs build`**) sitting
alongside the hand-written design docs, so the code's actual contract can be checked against intent.

- **API reference** — every `src/` module, and the `tests/` (what each unit test asserts).
- **Schema · TODO · Questions · Dev Setup** — the hand-written plan and notes to check the code against.

Preview locally with `uv run mkdocs serve` (http://127.0.0.1:8000); build the static site with
`uv run mkdocs build`. The project overview, business answers, and pipeline write-up are in the
repo's top-level `README.md`.
