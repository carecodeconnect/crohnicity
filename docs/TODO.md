# Implementation TODO

Deferred engineering tasks, kept here so they can be picked up directly in **plan mode**
later. These are intentionally *not* done yet — see `CLAUDE.md` ("Code style") for why
enforcement waits until we understand what to test and what to validate.

## Quality gates — manual check script (no pre-commit)

We deliberately **don't** use pre-commit hooks — overkill for this project. Enforcement is a
manual gate run on every code update (see `CLAUDE.md` → Code style).

- [x] `tests/check.sh` — runs `ruff check`, `ruff format --check`, `ty check`, and `pytest`
  (scoped to `src`/`tests`); run via `bash tests/check.sh`.
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
- [ ] **Domain-expert validation** of the consolidated `referral_pathway` phase vocabulary — a
  clinician must sign off on the canonical phases and their merges before they drive analysis,
  especially clinically loaded ones like `loss_of_response` (primary non-response vs. secondary
  loss of response).

## Orchestration — Dagster

- [ ] Wire the pipeline with **Dagster** (declared but not yet used). Run
  `src/referral_pathway_analysis.py` as the **final step** of the workflow — after extraction
  and aggregation — so the phase/transition table and the interactive journey graph are
  regenerated from the latest pathways on every run. (Note: the script currently uses a
  hardcoded `PATHWAYS` dict; wiring it into Dagster means switching it to read the
  `referral_pathway` column from the ground-truth/extracted data.)

## Packaging — Docker

- [ ] After the `src/` refactor, add a **Dockerfile** producing a **small image** (e.g.
  `python:3.14-slim` + `uv`), so the whole pipeline can be run and tested independently of the
  local environment and its dependencies.

## Polish

- [ ] **Duplicate title in the pathway graphs / MkDocs** — the per-case graph heading renders
  twice (e.g. `Referral pathway: P005` / `Referral pathway: P005`), likely the pyvis `heading`
  argument doubling up. De-duplicate in `src/referral_pathway_analysis.py` (`render`) and check
  the docs page.
