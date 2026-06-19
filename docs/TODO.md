# Implementation TODO

Deferred engineering tasks, kept here so they can be picked up directly in **plan mode**
later. These are intentionally *not* done yet — see `CLAUDE.md` ("Code style") for why
enforcement waits until we understand what to test and what to validate.

## Quality gates — manual check script (no pre-commit)

We deliberately **don't** use pre-commit hooks — overkill for this project. Enforcement is a
manual gate run on every code update (see `CLAUDE.md` → Code style).

- [x] `tests/type_lint_unit_tests.sh` — runs `ruff check`, `ruff format --check`, `ty check`, and `pytest`
  (scoped to `src`/`tests`); run via `bash tests/type_lint_unit_tests.sh`.
- [ ] (Optional) mirror the same checks in CI so the reviewer sees a green build.

## Refactor — notebooks → `src/` modules

Notebooks (`notebooks/`) are for prototyping only. Once the pipeline shape is settled,
extract the logic into proper Python modules.

- [ ] Move prototyped logic out of the notebooks into modules under `src/` (currently empty).
- [ ] Keep notebooks as thin exploration/drivers that import from `src/`, not as the source of truth.
- [ ] Mirror the module layout with `pytest` unit tests under `tests/` (currently empty) — this is the prerequisite for the Tests section below.

## Tests — once we have a mental model of what to test

- [ ] Add `pytest` tests under `tests/` (currently empty).
- [ ] Identify the units worth testing once the pipeline shape is clear, e.g.:
  - parsing the annotation columns from `interviews_ground_truth.xlsx` into the
    Pydantic model (see `docs/SCHEMA.md`),
  - extraction output conforming to the schema,
  - aggregation into the four business answers.

## Validation — decide which layer owns what, then test it

Pin down where each kind of validation belongs, document the decision, and back it with tests:

- [ ] **LiteLLM prompt-call boundary** — constrain model output with
  `response_format={"type": "json_object"}`, the Gemini `response_schema` hook, and
  optional `enforce_validation: true`.
- [ ] **Pydantic** — validate the parsed structured output against the model sketched
  in `docs/SCHEMA.md`.
- [ ] **pandas** — tabular sanity checks (nulls, duplicates, enum membership) before and
  after aggregating into the business answers.
- [ ] Write tests targeting whichever boundary we choose, so the gate is real rather than
  aspirational.

## Robustness — error handling + null semantics (NEXT, once the JSON loop runs)

When `extract` loops over every patient in `data/in/interviews.json`, harden both the *call* and
the *parse*. **Surface failures — never swallow them silently**: log via loguru, mark the record,
keep the batch going where sensible, but make every failure visible and countable.

- [ ] **Schema validation AND data-type validation** — not just "is it valid JSON" but "do the
  fields hold the right types / enum members" (Pydantic catches most; add pandas dtype/enum checks
  on the aggregated frame).
- [ ] Handle each failure mode with a distinct, logged outcome:
  - **Malformed JSON** (non-JSON or truncated model output).
  - **Schema validation failures** (`litellm.JSONSchemaValidationError`, Pydantic `ValidationError`).
  - **Rate limits / transient API errors** (back off + retry; e.g. `litellm` `num_retries`).
  - **Partial outputs** (required fields missing).
  - **Empty responses** (no content / empty `choices`).
- [ ] **Null semantics** — represent nulls in a Pydantic/pandas-compatible way that distinguishes
  genuinely **missing** (not stated -> `None`/NA) from **empty** (`[]`, `""`) and from **"doesn't
  apply"** (the `NOT_APPLICABLE` enum members), so a later pandas analysis can tell "we don't know"
  apart from "known to be none".
- [ ] **Per-record failure capture** — one bad patient must not abort the run; report how many and
  which records failed and why (counts + reasons logged, not hidden).

## Reference data — canonical lookup lists

- [ ] **Branded biologics registry.** Extract the biologic names mentioned across *all*
  transcripts (Remicade, Humira, Stelara, Entyvio, …) into a curated ground-truth list of
  canonical brand names — plus their generic/INN equivalents (infliximab, adalimumab,
  ustekinumab, vedolizumab) and the generic term "biologic". A single model/prompt searches
  each transcript against this list and matches/normalises mentions to populate
  `biologic_type`. Keeps extraction consistent and auditable instead of free-text.
- [ ] **Referral-pathway canonical points + journey types.** Build a controlled vocabulary of
  canonical journey events (e.g. `symptom_onset`, `misdiagnosis`, `specialist_referral`,
  `biologic_taken`, `insurance_denial`, `loss_of_response`) and higher-level journey-type
  categories to classify the circular/contradictory pathways. Cross-cutting pattern-finding
  across journeys will need LLM assistance; then link journey types to the other column
  values. This is its own work project — see the `referral_pathway` notes in `docs/SCHEMA.md`.
  - **Big post-MVP task.** A *minimal* `referral_pathway` prompt is in the MVP; the **refinement** is the major next step *after* it.
    The `PathwayStep` enum in `src/schema.py` is a minimal draft only (enough to render the
    example diagrams); refining the step vocabulary, the consolidation rules, and journey-type
    clustering will take substantial, dedicated iteration — likely its own project.
- [ ] **Domain-expert validation** of the consolidated `referral_pathway` phase vocabulary — a
  clinician must sign off on the canonical phases and their merges before they drive analysis,
  especially clinically loaded ones like `loss_of_response` (primary non-response vs. secondary
  loss of response).

## Pipeline coordinator — `src/main.py`

Once each component is built and tested (schema, `extract`/`save`, splits, referral-pathway
render, and aggregation into the four answers), add a **minimal `src/main.py`** that wires them
into one pipeline in the simplest way — load `data/in/interviews.json`, loop `extract` over each
patient, persist predictions, then aggregate. Keep it a plain script; the **Dagster orchestration
below comes after** this runs end-to-end.

## Orchestration — Dagster

- [ ] Wire the pipeline with **Dagster** (declared but not yet used). Run
  `src/referral_pathway_analysis.py` as the **final step** of the workflow — after extraction
  and aggregation — so the phase/transition table and the interactive journey graph are
  regenerated from the latest pathways on every run. (Note: the script currently uses a
  hardcoded `PATHWAYS` dict; wiring it into Dagster means switching it to read the
  `referral_pathway` column from the ground-truth/extracted data.)
- [ ] **Automate the runs once the pipeline works** — orchestrate extraction + the test harness
  via Dagster (sensor/schedule), and **log each run** (inputs, predictions, accuracy, token
  usage) for reproducibility and later optimisation.

## Metrics & EDA — API-call telemetry

What each call exposes (tokens, cached tokens, cost, latency, call metadata) and the two ways to
read it — the `ModelResponse` in `extract()` vs the `RAW RESPONSE` in `logs/litellm_debug.log` —
are documented in [`TELEMETRY.md`](TELEMETRY.md). We want this for **cost/latency optimisation and
scaling EDA**.

- [ ] **Capture per-call telemetry structurally** (don't scrape logs): persist tokens, cached
  tokens, cost, latency, `finish_reason`, and `model_version` per patient alongside the prediction.
- [ ] **EDA plots**: tokens & cost per case, cache-hit rate, latency distribution, and totals to
  project cost at scale. Ties into the Dagster "log each run" item above.

## Packaging — Docker

- [ ] After the `src/` refactor, add a **Dockerfile** producing a **small image** (e.g.
  `python:3.14-slim` + `uv`), so the whole pipeline can be run and tested independently of the
  local environment and its dependencies.

## Polish

- [ ] **Duplicate title in the pathway graphs / MkDocs** — the per-case graph heading renders
  twice (e.g. `Referral pathway: P005` / `Referral pathway: P005`), likely the pyvis `heading`
  argument doubling up. De-duplicate in `src/referral_pathway_analysis.py` (`render`) and check
  the docs page.
