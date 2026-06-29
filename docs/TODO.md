# Implementation TODO

Deferred engineering tasks, kept here so they can be picked up directly in **plan mode**
later. These are intentionally *not* done yet — see `CLAUDE.md` ("Code style") for why
enforcement waits until we understand what to test and what to validate.

## Extraction run — status

`data/out/` is the **final `temperature = 0` snapshot**: all 50 predictions regenerated in one clean
run and the README re-renders from that consistent set (the provisional-run note in README → *Answers*
has been removed).

- [x] **Clean `temperature = 0` full re-run.** All 50 predictions regenerated at `temperature = 0`
  (deterministic) from one run; `README.md` re-rendered from the consistent set.
- [ ] **EDA plot P-id clarity** (the *EDA plot clarity* items in the final-sweep section below). The
  Q2 `(null)→unspecified` and Q3 biologic-mislabel **prompt fixes are now in
  `data/prompts/system.txt`** and `data/out/` **was regenerated and reflects them** (P047 =
  `['NOT_APPLICABLE']`, P048 = `['DEFERRED']`, P046 no longer mislabelled). What stays open here is the
  *plot-presentation* polish (titles / N annotation) tracked in the final-sweep section below.

## Next step — resolve the P019 `to_review` inconsistency

P019 is `to_review = 0` yet carries a gold `biologic_taken = 1`, and `docs/TO_REVIEW.md` discusses it
as reviewed — an internal inconsistency. **Decide whether P019 should be `to_review = 1`.** If set, it
enters `gold_eval`: the reviewed set goes **21 → 22** and the eval **n goes 20 → 21** (P019's
`biologic_taken` is non-null and the model predicts `True`), which shifts the documented metrics and
the `test_gold_eval_matches_documented_metrics` assertion (verified via the gold/eval audit). Flagged
here, not changed silently.

## Prompt — cover every field (next task)

- [x] **Build up the single system prompt** (`data/prompts/system.txt`) with explicit guidance for
  *every* field in `PatientLabels` — not just `churn`, `biologic_timing`, `referral_pathway` — so
  each label (biologic funnel, reasons, comorbidities, treatment outcomes, demographics) is
  populated deliberately rather than left to the model's defaults. Single prompt for this version;
  the concurrent multi-prompt split is a post-completion idea (README → Next Steps) — and the place
  where *explicit, inspectable* chain-of-thought earns its keep: it fixes the single-shot
  attention-competition behind shaky `churn`/`referral_pathway`/`biologic_timing` **and** gives a
  reviewer auditable intermediates, as opposed to the *opaque* internal thinking now disabled
  (`reasoning_effort="disable"` → `thinkingBudget=0`). Turn off opaque thinking now, add explicit
  staged CoT later — complementary, not contradictory.
- [x] **Revisit `system.txt` in light of the post-extraction EDA** — folded in the prompt adjustments the
  EDA surfaced (e.g. churn detection, enum-coverage gaps like Q2's `DOCTOR_CHOICE`/`ACCESS`,
  under-populated or over-defaulted fields, the P047 biologic over-detection and the P047/P048
  `reasons_for_biologic_not_taken` gap). The churn guidance was refined from the `TO_REVIEW.md` audit
  (P016/P019/P049), and `data/out/` was regenerated so the predictions reflect the updated prompt.

## Chunked extraction — batched calls (free-tier RPD workaround)

- [x] `--chunk-size N` on `src/main.py` sends N transcripts per Gemini call via `extract_batch()` +
  a `BatchPredictions` wrapper, so 50 patients fit the **20-requests/day** free-tier cap (10×5 = 5
  calls). Per-call telemetry (`total_tokens`, `cost`) is logged to `logs/extract.log` so token
  usage + calls/day are monitorable by grepping the log. A malformed chunk no longer fails the run:
  `run_chunked` **skips + logs** the bad chunk (counts the skipped patients) and continues; a
  tolerant *per-record* salvage within a chunk is future hardening (see Robustness). Reuses the
  existing loguru logging; no new infrastructure.

## Quality gates — manual check script (no pre-commit)

We deliberately **don't** use pre-commit hooks — overkill for this project. Enforcement is a
manual gate run on every code update (see `CLAUDE.md` → Code style).

- [x] `tests/type_lint_unit_tests.sh` — runs `ruff check`, `ruff format --check`, `ty check`, and `pytest`
  (scoped to `src`/`tests`); run via `bash tests/type_lint_unit_tests.sh`. Green: 19 passed.
- [ ] (Optional) mirror the same checks in CI so the reviewer sees a green build.

## Refactor — notebooks → `src/` modules

Notebooks (`notebooks/`) are for prototyping only. Once the pipeline shape is settled,
extract the logic into proper Python modules.

- [x] Move prototyped logic out of the notebooks into modules under `src/` (7 modules: `config`,
  `schema`, `extract`, `main`, `pipeline`, `post_extraction_eda`, `referral_pathway_analysis`).
- [x] Keep notebooks as thin exploration/drivers that import from `src/`, not as the source of truth.
- [x] Mirror the module layout with `pytest` unit tests under `tests/` — this is the prerequisite for the Tests section below.

## Post-extraction EDA — extract `README.qmd` chunks into `src/post_extraction_eda.py`

The post-extraction EDA is a distinct **phase**: it runs *after* the inference loop and reads only
the persisted artefacts in `data/out/` (the validated predictions, plus `_v7.ods` for the gold
eval) — no Gemini calls. Its logic currently lives inline in the `README.qmd` `{python}` cells, so
it can't be reused anywhere else or unit-tested.

- [x] **Move each `README.qmd` code cell into a reusable function** in `src/post_extraction_eda.py`
  — e.g. `load_predictions(out_dir) -> DataFrame`, `q1_share(df)`, `gold_eval(df, gold)`,
  `q2_reasons(df)`, `q3_before_biologic(records)`, `q4_steps(records)`, `churn_three_state(df)`.
  Pure functions over the `data/out/` artefacts — **reusable anywhere** (notebooks, the QMD, tests,
  a future Dagster asset).
- [x] **The QMD cells then just import and call** these functions, so `README.qmd` holds only
  presentation (tables/plots/prose) and `src/` holds the computation — the same notebooks→`src/`
  split (above) applied to the report.
- [x] **Cover the functions with `pytest`** (now importable + deterministic over fixed artefacts) and
  bring them under the `tests/type_lint_unit_tests.sh` gate (`tests/test_post_extraction_eda.py`).
- [ ] **Plot the eval metrics.** Add a **precision / recall / F1** (and accuracy) bar plot beside the
  Q1 gold-eval table in `README.qmd`, driven by `gold_eval(df)` — same plotnine treatment as the
  Q2–Q4 charts — so the eval is visual, not just a table.
- [ ] **Visualise gold coverage + its uncertainty.** A plot showing only **21/50** patients are
  manually gold-scored (the `to_review` reviewed set; 20 with a non-null `biologic_taken`) vs the **~29/50**
  with **unknown** ground truth, plus a **confidence interval** on the implied at-scale accuracy
  (e.g. a Wilson / binomial CI, or bootstrap, on the 20-case metrics) — so the README's *sampling
  uncertainty* caveat is **quantified and shown**, not merely asserted.

## Tests — once we have a mental model of what to test

- [x] Add `pytest` tests under `tests/` (6 test files; gate green at 19 passed).
- [x] Identify the units worth testing once the pipeline shape is clear, e.g.:
  - parsing the annotation columns from `interviews_ground_truth.xlsx` into the
    Pydantic model (see `docs/SCHEMA.md`),
  - extraction output conforming to the schema,
  - aggregation into the four business answers.

## Validation — decide which layer owns what, then test it

Pin down where each kind of validation belongs, document the decision, and back it with tests:

- [x] **LiteLLM prompt-call boundary** — constrain model output with
  `response_format={"type": "json_object"}`, the Gemini `response_schema` hook, and
  `enforce_validation: true` (`src/extract.py`).
- [x] **Pydantic** — validate the parsed structured output against the model sketched
  in `docs/SCHEMA.md` (`PatientLabels.model_validate_json` in `src/extract.py`).
- [ ] **pandas** — tabular sanity checks (nulls, duplicates, enum membership) before and
  after aggregating into the business answers.
- [x] Write tests targeting whichever boundary we choose, so the gate is real rather than
  aspirational (`tests/test_extract.py`).

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
- [x] **Null semantics** — represent nulls in a Pydantic/pandas-compatible way that distinguishes
  genuinely **missing** (not stated -> `None`/NA) from **empty** (`[]`, `""`) and from **"doesn't
  apply"** (the `NOT_APPLICABLE` enum members), so a later pandas analysis can tell "we don't know"
  apart from "known to be none".
- [x] **Per-record failure capture** — done at the **chunk** grain: a failed chunk is skipped + the
  skipped patient ids counted and logged, so one bad chunk can't abort the run (`run_chunked` in
  `src/main.py`). Per-*record* salvage *within* a chunk is still future hardening (see below).

## Determinism — pin decoding params

- [x] **Pin `temperature=0`** (greedy) on the `litellm.completion` calls in `src/extract.py` (`TEMPERATURE`
  from `config.json`), to minimise extraction sampling variance, and the clean re-run regenerated
  `data/out/` at that setting. Structured-output mode + the persisted `data/out/` artefacts are the
  hard reproducibility guarantee (see README → Extraction Pipeline → Determinism); a `seed` would add
  belt-and-braces but isn't wired (with reasoning disabled, `0` already minimises drift).

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
  categories to classify the circular/contradictory pathways — **clustering each case by its
  sequence of `PathwayStep` tokens** (those step components are the clustering features).
  Cross-cutting pattern-finding across journeys will need LLM assistance; then link the resulting
  journey types to the other column values. This is its own work project — see the `referral_pathway` notes in `docs/SCHEMA.md`.
  - **Big post-MVP task.** A *minimal* `referral_pathway` prompt is in the MVP; the **refinement** is the major next step *after* it.
    The `PathwayStep` enum in `src/schema.py` is a minimal draft only (enough to render the
    example diagrams); refining the step vocabulary, the consolidation rules, and journey-type
    clustering will take substantial, dedicated iteration — likely its own project.
- [ ] **Domain-expert validation** of the consolidated `referral_pathway` phase vocabulary — a
  clinician must sign off on the canonical phases and their merges before they drive analysis,
  especially clinically loaded ones like `loss_of_response` (primary non-response vs. secondary
  loss of response).

## Pipeline coordinator — `src/main.py`

Once each component is built and tested (schema, `extract`/`save`, referral-pathway
render, and aggregation into the four answers), add a **minimal `src/main.py`** that wires them
into one pipeline in the simplest way — load `data/in/interviews.json`, loop `extract` over each
patient, persist predictions, then aggregate. Keep it a plain script; the **Dagster orchestration
below comes after** this runs end-to-end.

## Orchestration — Dagster

**Design decision — Dagster is the day-of entry point.** `uv run dagster dev -f src/pipeline.py` is
THE "full" run: it auto-orchestrates the whole end-to-end pipeline (ingest → extract → validate →
aggregate → referral-pathway render → post-extraction EDA) and **flags problems at a high level in
the UI**. The `src/main.py` CLI and the `.sh`/`.py` scripts stay runnable **standalone**, to
test/show one sub-part on demand — they are *not* nested under Dagster. This works because **both
the CLI and the Dagster assets call the same `src/` functions** (library-first: an asset *wraps* a
function; it does not shell out to `uv run python src/main.py`). Verification becomes Dagster **asset checks**, not just a standalone gate: the
`tests/type_lint_unit_tests.sh` gate — **ruff** (lint), **ruff format**, **`ty`** (typing) and
**`pytest`** (unit tests) for the repo — plus the render smoke test, expressed as
`@dg.asset_check`s so a failed lint / type-check / test lights up **red in the same UI** alongside
the data assets (these check the *code* rather than a data artefact; the asset check just surfaces
them at a glance). Plain `bash tests/type_lint_unit_tests.sh` stays available for a quick headless run. This is the
payoff of, and depends on, the "notebooks → `src/`" and "post-extraction EDA →
`src/post_extraction_eda.py`" refactors above: once every stage is an importable function, both
frontends compose the same units.

**Static input → no sensor this version.** `data/in/interviews.json` is the single **static,
committed** input — the `interviews` source asset always reads it as-is; the pipeline **never
re-downloads or re-fetches** it. So there is **no Dagster sensor/schedule** watching for new data;
the full run is **manual / on-demand** (materialise the assets in the UI). A sensor/schedule only
earns its place once the input becomes *dynamic* — e.g. new transcripts arriving via the FastAPI
endpoint in the README's Next Steps.

- [ ] **Per-stage dependency graph for failure visibility.** `src/pipeline.py` is a minimal start
  (`interviews` → `predictions`). Expand to distinct assets/ops at **each stage — data ingestion →
  transformation → model call → schema validation** — so a failure is pinpointed at *any* point,
  ideally per-patient (the UI shows which transcript failed where, not just the whole batch).
- [x] Wire the pipeline with **Dagster**. `src/pipeline.py` runs the graph
  `interviews -> predictions -> {referral_graphs, readme, referral_pathways_md -> docsite}`, with
  `referral_pathway_analysis` (the `referral_graphs` asset) downstream of `predictions` so the
  phase/transition table and the interactive journey graphs are regenerated from the latest pathways
  on every run. The script now reads the `referral_pathway` lists from the persisted predictions
  (`data/out/json/P*.json`) — the hardcoded `PATHWAYS` dict is gone.
- [x] **Doc/report artifacts as final assets (orchestrated).** The **README render**
  (`quarto render README.qmd`), the **referral graphs**, and **`referral_pathways_md`**
  (`quarto render docs/referral_pathways.qmd`) are downstream assets of `predictions` (they read
  `data/out/`). The **docsite** (`mkdocs build`) **depends on `referral_pathways_md`** — *not* an
  independent asset — because the journey gallery (`docs/referral_pathways.md`) is rendered from the
  predictions and must be fresh before mkdocs copies it; the rest of the site documents source
  *docstrings*. One orchestrated run then regenerates every code+data artifact with per-step status
  in the UI.
- [x] **Dagster run logging -> `logs/`.** An unfiltered loguru sink in `src/pipeline.py` captures the
  whole orchestrated run (the in-process extract/referral assets log via loguru) to `logs/dagster.log`,
  so the run is auditable in one place. **`DAGSTER_HOME`** is set (in `.env`, pointing at the
  git-ignored `.dagster_home/` with a committed `dagster.yaml`) so run history persists.
- [x] **Migrate to the `dg` CLI (`dg dev`).** Done: `dagster-dg-cli` is a dependency, a
  `[tool.dg.project]` block in `pyproject.toml` points at the `src` root module, and the entry point
  is now `uv run dg dev -m pipeline -d src -p 3050` (no more `dagster dev -f` `SupersessionWarning`).
- [ ] **Automate the runs once the pipeline works** — orchestrate extraction + the test harness
  via Dagster, and **log each run** (inputs, predictions, accuracy, token usage) for
  reproducibility and later optimisation. (A **sensor/schedule** is deferred — see the static-input
  note above; it's only warranted once the input is dynamic.)

## Metrics & EDA — API-call telemetry

What each call exposes (tokens, cached tokens, cost, latency, call metadata) and the two ways to
read it — the `ModelResponse` in `extract()` vs the `RAW RESPONSE` in `logs/litellm_debug.log` —
are documented in [`TELEMETRY.md`](TELEMETRY.md). We want this for **cost/latency optimisation and
scaling EDA**.

- [ ] **Capture per-call telemetry structurally** (don't scrape logs): persist tokens, cached
  tokens, cost, latency, `finish_reason`, and `model_version` per patient alongside the prediction.
- [ ] **EDA plots**: tokens & cost per case, cache-hit rate, latency distribution, and totals to
  project cost at scale. Ties into the Dagster "log each run" item above.

## Reporting — Quarto → GFM

- [x] **`README.qmd` business answers.** `README.qmd` **dynamically generates the plots and tables**
  answering the four PharmaCorp questions (Q1–Q4) — with the per-case `referral_pathway` diagrams —
  by importing `src/post_extraction_eda.py`, and renders to **GitHub-flavoured markdown** (`README.md`,
  Q1 = 74% / 37-of-50) via `quarto render`. A static, version-controlled answers doc that refreshes
  from the latest predictions.
- [x] **System-design diagram.** `docs/DESIGN.qmd` was renamed to **`docs/SYSTEM_DESIGN.qmd`** (rendered
  to `docs/SYSTEM_DESIGN.md`) — a Quarto **Mermaid** chart of the real workflow clarifying the
  **Dagster / `uv run` relation**: `uv run dg dev -m pipeline -d src` is the orchestrating entry point,
  while `uv run python src/main.py` (CLI) and the `.sh` gate run the *same* `src/` functions
  **standalone** (library-first, not nested); static `data/in/interviews.json` input → no sensor. It is
  **linked from `README.qmd`** (multiple places), and the draft's stale bits (title, `_v7.ods`, the
  Dagster asset graph) are fixed.

## Packaging — Docker

- [ ] After the `src/` refactor, add the **simplest possible Dockerfile** producing the **smallest
  image** for this use case (e.g. `python:3.14-slim` + `uv sync --frozen`), so the whole pipeline can
  be built, run and tested **on any machine** independently of the local environment — the
  cross-machine reproducibility check (does it run off my laptop?).

## Final clean-up sweep — before the final build

The last pass before finalising, **after** the pipeline runs end-to-end. Do **all** of:

- [x] **Centralise config in a `config.json`.** Every setting is loaded via `src/config.py` from one
  `config.json` (model default, gold path/version `_v7.ods`, the `interviews.json` path, `data/out/`
  locations, `chunk_size`, retry, ports, `max_tokens`, `temperature`), imported across `extract.py` /
  `main.py` / `pipeline.py` / `post_extraction_eda.py` / `referral_pathway_analysis.py` / `README.qmd`.
  The app version is sourced from `pyproject.toml` via `config.APP_VERSION`. A single source of truth.
- [ ] **Kill redundancy + fix drift.** Version drift **resolved** — the schema version lives once in
  `SCHEMA.md`, the mkdocs nav + README dropped the duplicate, and the app version is sourced from
  `pyproject.toml` via `config.APP_VERSION`; `_v3`/`_v4` mentions bumped to `_v7`; `DESIGN.qmd` →
  `SYSTEM_DESIGN.qmd`. Remaining: scan for any duplicated setup text / drifted docstrings before the final build.
- [ ] **Every TODO item addressed** (this file) — each one done, or consciously moved to
  README → *Next Steps* as post-MVP.
- [ ] **Every question answered** — cross-check `docs/TASK_INSTRUCTIONS.md` *and* `README.qmd`: all
  four business questions *and* the schema / pipeline / evaluation dev-questions carry a written
  answer (no prompt-only sections left). This is the last gate before CAIO handover.
- [x] **Docsite builds complete.** `uv run mkdocs build` covers *all* `src/` modules + tests via
  mkdocstrings — `api/src.md` covers all 7 src modules (config, schema, extract, main, pipeline,
  post_extraction_eda, referral_pathway_analysis) and `api/tests.md` covers the tests.
- [ ] **EDA plot clarity + correctness (diagnosed; fix in final sweep).**
  - **Q2 `(null)` -> `unspecified`** — relabelled in `q2_reasons`; the underlying prompt gap is now
    **fixed in `data/out/`** (the prompt requires a `ReasonNotTaken`): P047 = `['NOT_APPLICABLE']`,
    P048 = `['DEFERRED']` in the regenerated predictions. Remaining: the plot-presentation polish.
  - **Q3 "treatments before a biologic" includes biologics** — the P046 mislabel is **fixed in
    `data/out/`** (P046 is now `biologic_taken=True`, `['BIOLOGIC_TAKEN']`, no longer `BEFORE`). Still
    open is the plot title/definition: clarify whether Q3 counts earlier/switched biologics (e.g. P043's
    genuine Remicade->Humira switch) or only non-biologic treatments, and annotate the plot accordingly.
  - **Q4 `q4_steps.png`** — annotate with **N** (cohort size, n=50) so the population is visible on the plot.

- [ ] **Security check before handover.** Confirm the GitHub repo is **private**
  (`gh repo view --json visibility`) and the **`.gitignore` is correct** — `.env` (the only secret,
  `GEMINI_API_KEY`), `.venv/`, `site/`, and the Dagster run-state (`logs/dagster/*` except
  `dagster.yaml`) are all ignored, and `git ls-files` lists no credentials or unintended files. The
  synthetic `data/in` / `data/out` are committed *deliberately* — see README → *Data handling & privacy*.

## Polish

- [x] **Duplicate title in the pathway graphs / MkDocs** — fixed: `render` in
  `src/referral_pathway_analysis.py` collapses the doubled pyvis `heading` to a single page-level
  `<h1>` (`html.rsplit(dup, 1)` when the count exceeds one); verified one heading per rendered
  `data/out/html/referral_pathway_*.html`.
