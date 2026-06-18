# Implementation TODO

Deferred engineering tasks, kept here so they can be picked up directly in **plan mode**
later. These are intentionally *not* done yet — see `CLAUDE.md` ("Code style") for why
enforcement waits until we understand what to test and what to validate.

## Quality gates — enforce the toolchain with pre-commit

- [ ] Add `pre-commit` as a dev dependency and create `.pre-commit-config.yaml`.
- [ ] Hook: `ruff check` (lint) on commit.
- [ ] Hook: `ruff format` (format) on commit.
- [ ] Hook: `ty check` (type-check) on commit.
- [ ] `pre-commit install`, and document the step in `CLAUDE.md` → Commands.
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
