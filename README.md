# Crohnicity

Crohnicity is a prototype data-extraction pipeline for a health-tech setting. It turns 50 messy,
free-text patient interview transcripts about Crohn's disease into structured, validated, evaluated
records, and uses that structured output to answer four commercial questions about the treatment
landscape.

It is built as an **AI-engineering / data-science** exercise: pulling trustworthy structured data
out of unstructured natural-language text with a large language model, wrapped in the
software-engineering practices that make an LLM pipeline reproducible, testable, and auditable rather
than a one-off script.

The full, **data-generated** write-up — the four business answers, the schema rationale, the
evaluation against a hand-labelled gold set, and the churn/limitations discussion — lives in
**[docs/SOLUTION.md](docs/SOLUTION.md)**. This README is the high-level overview.

## The problem it solves

Health-tech and health-analytics teams sit on large volumes of unstructured patient narratives —
interview transcripts, intake notes, support conversations. That text carries exactly the signal the
business needs (what treatments people are on, why they stopped, where they are in a referral
pathway), but in a form no dashboard or SQL query can touch. Turning messy text into clean, typed,
trustworthy records is the recurring, high-value task behind a lot of applied-ML and AI-engineering
work — especially in health tech, where the same job shows up as clinical-note extraction, symptom
coding, and patient-journey analytics.

Crohnicity is a small, honest, end-to-end example of that task:

- **Messy input, structured output.** Transcripts of varying length and completeness — some clear,
  some vague, some cut off mid-sentence — become one validated record per patient.
- **Uncertainty as a first-class signal.** The schema keeps "not mentioned", "explicitly denied",
  and "the interview was cut off before we found out" as *distinct* states rather than collapsing
  them into a single null, because they mean different things to the analysis.
- **Answers with caveats.** The structured output is aggregated into four business questions, each
  reported with its evaluation evidence and the limitations behind it, not as bare numbers.

## What it produces

The four questions it answers (a pharma commercial team preparing to launch a Crohn's biologic wants
to understand the landscape it is entering):

1. What share of patients appear to be on a biologic?
2. For patients not on a biologic, what are the primary reasons?
3. What other treatments are commonly tried before a biologic?
4. What does a typical referral pathway look like, in steps to a biologic-prescribing specialist?

The answers, with the evaluation and the caveats that matter, are in
[docs/SOLUTION.md](docs/SOLUTION.md).

## System design

High-level flow (full diagram and rationale in
[docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)):

```
interviews.json  ->  extraction (LiteLLM -> Gemini, structured output)
                 ->  Pydantic validation  ->  one persisted JSON per patient
                 ->  post-extraction analysis (pandas)
                 ->  reporting (Quarto + MkDocs)
```

- **Extraction.** One structured LLM call per patient (batched several patients per request to fit
  the free-tier request cap), constrained to a Pydantic-derived JSON schema so the model *cannot*
  return values outside the controlled vocabularies.
- **Validation.** Every response is validated against the schema at the call boundary and again when
  it is loaded for analysis.
- **Determinism.** Temperature is pinned to 0 and model reasoning is disabled — extraction is a
  classification task, not multi-step inference — and the persisted per-patient JSON is the real
  reproducibility guarantee: the analysis reads only those frozen artefacts, so every number and plot
  is stable run to run.
- **Evaluation.** Predictions are scored field by field against a gold set hand-labelled by the
  author, so the write-up can state where the pipeline is solid and where it is shaky.
- **Orchestration.** Dagster runs ingest → extract → analysis → reporting as a dependency graph, so a
  failure is pinpointed by stage rather than lost in a monolithic script.

The single source of truth for runtime values (model, paths, decoding params) is
[`config.json`](config.json); the schema is defined once in [`src/schema.py`](src/schema.py)
(documented in [docs/SCHEMA.md](docs/SCHEMA.md)); changes between runs are recorded in
[CHANGELOG.md](CHANGELOG.md).

## Tech stack

| Concern | Choice | Why it's here |
|---|---|---|
| Language / env | Python 3.14, managed with `uv` | Fast, reproducible dependency + venv management |
| LLM gateway | **LiteLLM** → **Gemini** | One provider-agnostic interface; the working model is set in [`config.json`](config.json) |
| Schema / validation | **Pydantic** | Types the output and enforces enum membership at the model boundary |
| Analysis | **pandas** | Aggregation into the business answers + the gold-set evaluation |
| Orchestration | **Dagster** | Per-stage dependency graph with failure visibility |
| Reporting | **Quarto** + **MkDocs** / mkdocstrings | Data-generated solution write-up + an API docsite from docstrings |
| Quality gate | **ruff**, **ty**, **pytest** (Rust-based toolchain) | Lint, type-check, and tests run on every change |

Read as a portfolio piece, the stack is deliberately the shape of an applied **AI-engineering /
health-tech** role: LLM-based information extraction, prompt design and structured output,
schema-enforced validation, a real evaluation harness, and a reproducible, orchestrated pipeline —
the "prompts, evals, and pipelines" core rather than a notebook.

## How I worked with AI (a careful, sceptical approach)

I built this with an AI coding assistant, but deliberately conservatively. I designed the pipeline
and the Pydantic schema by hand first, from repeated close reads of the spec, and hand-labelled the
gold set myself. From there I used the assistant for most of the implementation but questioned every
decision: I ran the tests and pipelines in a separate terminal so I was never trusting the
assistant's *reported* output, did all `git` operations myself, and only accepted a change after
reviewing its diff. The approach was test-, data-, log-, and doc-driven, so I could inspect the
output at every stage and compare it against an expected version.

The full first-person account — what I did with AI and what I deliberately did without it — is in the
"Where I used AI" section of [docs/SOLUTION.md](docs/SOLUTION.md).

## Programmatic reporting with Quarto

[docs/SOLUTION.md](docs/SOLUTION.md) is **generated from the data**, not written by hand. It is a
Quarto document whose code chunks read the persisted predictions and render the tables, plots, and
headline figures at build time, so every number refreshes from the latest run and nothing is pasted
in or left to drift. Literate, code-driven reporting is common in the R world but still unusual in
Python; using it here keeps the analysis and the document that describes it in lockstep — the same
discipline that keeps the rest of the repo on a single source of truth.

## Background

The approach is grounded in Agrawal, Hegselmann, Lang, Kim & Sontag,
[*"Large language models are few-shot clinical information extractors"*](https://aclanthology.org/2022.emnlp-main.130/)
(EMNLP 2022) — the finding that general-purpose LLMs, given a well-designed prompt and output schema,
can extract structured clinical information from unstructured text without task-specific training.
Crohnicity applies that idea with production-oriented guardrails around it: an enforced schema, a
gold-set evaluation, pinned decoding for determinism, and orchestration.

## Usage

The commands are the canonical set in [CLAUDE.md → Commands](CLAUDE.md#commands); the full local
setup is in [docs/DEV_SETUP.md](docs/DEV_SETUP.md). The short version:

```bash
uv sync                                      # install the pinned environment
bash tests/type_lint_unit_tests.sh           # the quality gate: ruff + ty + pytest
uv run dg dev -m pipeline -d src -p 3050      # Dagster UI -> "Materialize all"
```

A `GEMINI_API_KEY` in `.env` is required for the extraction step; the analysis and reporting steps
read only the committed `data/out/` artefacts and make no API calls.

## Roadmap

The next step is to expose the extractor as a **FastAPI** endpoint, **Dockerised** for local hosting,
on the same Gemini/LiteLLM infrastructure — turning the batch pipeline into a service that structures
a single transcript on request.

## Repository

```
src/         pipeline modules (schema, extract, config, main, pipeline, EDA, referral analysis)
tests/       pytest suite + the quality-gate script
data/        in/ committed input (interviews + gold) - out/ generated artefacts - prompts/
docs/        SOLUTION (the data-generated write-up), SYSTEM_DESIGN, SCHEMA, and design notes
config.json  single source of truth for runtime values
```

Further reading: [docs/SOLUTION.md](docs/SOLUTION.md) (the full solution),
[docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) (architecture),
[docs/SCHEMA.md](docs/SCHEMA.md) (the annotation schema), [CHANGELOG.md](CHANGELOG.md) (what changed
between runs), and [docs/TODO.md](docs/TODO.md) (next steps).
