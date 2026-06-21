# Implementation TODO

Deferred engineering tasks, kept here so they can be picked up directly in **plan mode**
later. These are intentionally *not* done yet — see `CLAUDE.md` ("Code style") for why
enforcement waits until we understand what to test and what to validate.

## Tomorrow — pre-interview (do first, once the daily quota resets)

The day's extraction hit Gemini's free-tier **daily quota** mid-run, so `data/out/` is a *provisional*
snapshot (an early chunk at `temperature = 0`, the rest from an earlier default-`1.0` run — see the
provisional-run note in README → *Answers*). Once the quota resets:

- [ ] **Clean `temperature = 0` full re-run.** Materialise the whole Dagster graph (`uv run dg dev -m
  pipeline -d src` → *Materialize all*) so all 50 predictions regenerate at `temperature = 0` and the
  README re-renders from one consistent set. **This is the only thing that makes today's provisional
  snapshot final.**
- [ ] **EDA plot P-id clarity** (the *EDA plot clarity* items in the final-sweep section below). The
  Q2 `(null)→unspecified` prompt fix and the Q3 biologic-mislabel fix only **take effect after a fresh
  extraction run**, so apply them on the same re-run rather than today.

## Prompt — cover every field (next task)

- [ ] **Build up the single system prompt** (`data/prompts/system.txt`) with explicit guidance for
  *every* field in `PatientLabels` — not just `churn`, `before_biologic`, `referral_pathway` — so
  each label (biologic funnel, reasons, comorbidities, treatment outcomes, demographics) is
  populated deliberately rather than left to the model's defaults. Single prompt for this version;
  the concurrent multi-prompt split is a post-completion idea (README → Next Steps).
- [ ] **Revisit `system.txt` in light of the post-extraction EDA** — fold in prompt adjustments the
  EDA surfaces (e.g. churn detection accuracy, enum-coverage gaps like Q2's `DOCTOR_CHOICE`/`ACCESS`,
  under-populated or over-defaulted fields). The churn guidance was already refined from the
  `TO_REVIEW.md` audit (P016/P019/P049); the EDA's reported distributions may surface more, and any
  change requires a fresh extraction run to take effect (current `data/out/` predates it).

## Chunked extraction — batched calls (free-tier RPD workaround)

- [x] `--chunk-size N` on `src/main.py` sends N transcripts per Gemini call via `extract_batch()` +
  a `BatchPredictions` wrapper, so 50 patients fit the **20-requests/day** free-tier cap (10×5 = 5
  calls). Per-call telemetry (`total_tokens`, `cost`) is logged to `logs/extract.log` so token
  usage + calls/day are monitorable by grepping the log. **Strict** parse (a malformed chunk fails
  wholly) — minimal; a tolerant per-record parse is future hardening (see Robustness). Reuses the
  existing loguru logging; no new infrastructure.

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

## Post-extraction EDA — extract `README.qmd` chunks into `src/post_extraction_eda.py`

The post-extraction EDA is a distinct **phase**: it runs *after* the inference loop and reads only
the persisted artefacts in `data/out/` (the validated predictions, plus `_v5.ods` for the gold
eval) — no Gemini calls. Its logic currently lives inline in the `README.qmd` `{python}` cells, so
it can't be reused anywhere else or unit-tested.

- [ ] **Move each `README.qmd` code cell into a reusable function** in `src/post_extraction_eda.py`
  — e.g. `load_predictions(out_dir) -> DataFrame`, `q1_biologic_share(df)`, `q1_gold_eval(df, gold)`,
  `q2_reasons(df)`, `q3_before_biologic(records)`, `q4_steps(records)`, `churn_three_state(df)`.
  Pure functions over the `data/out/` artefacts — **reusable anywhere** (notebooks, the QMD, tests,
  a future Dagster asset).
- [ ] **The QMD cells then just import and call** these functions, so `README.qmd` holds only
  presentation (tables/plots/prose) and `src/` holds the computation — the same notebooks→`src/`
  split (above) applied to the report.
- [ ] **Cover the functions with `pytest`** (now importable + deterministic over fixed artefacts) and
  bring them under the `tests/type_lint_unit_tests.sh` gate.
- [ ] **Plot the eval metrics.** Add a **precision / recall / F1** (and accuracy) bar plot beside the
  Q1 gold-eval table in `README.qmd`, driven by `gold_eval(df)` — same plotnine treatment as the
  Q2–Q4 charts — so the eval is visual, not just a table.
- [ ] **Visualise gold coverage + its uncertainty.** A plot showing only **20/50** patients are
  manually gold-scored (the `to_review` split; 19 with a non-null `biologic_taken`) vs the **~30/50**
  with **unknown** ground truth, plus a **confidence interval** on the implied at-scale accuracy
  (e.g. a Wilson / binomial CI, or bootstrap, on the 19-case metrics) — so the README's *sampling
  uncertainty* caveat is **quantified and shown**, not merely asserted.

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

## Determinism — pin decoding params

- [ ] **Pin `temperature=0`** (greedy) on the `litellm.completion` calls in `src/extract.py`, and pass
  a `seed` where Gemini honours it, to minimise extraction sampling variance. Today only structured-
  output mode + the persisted `data/out/` artefacts guarantee reproducibility (see README → Extraction
  Pipeline → Determinism); this is the remaining decoding-side lever. A change requires a fresh run to
  take effect (current `data/out/` predates it).

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
- [ ] Wire the pipeline with **Dagster** (declared but not yet used). Run
  `src/referral_pathway_analysis.py` as the **final step** of the workflow — after extraction
  and aggregation — so the phase/transition table and the interactive journey graph are
  regenerated from the latest pathways on every run. (Note: the script currently uses a
  hardcoded `PATHWAYS` dict; wiring it into Dagster means switching it to read the
  `referral_pathway` column from the ground-truth/extracted data.)
- [ ] **Doc/report artifacts as final assets (decided — orchestrate them).** Make the **README
  render** (`quarto render README.qmd`) and the **referral graphs** downstream assets of
  `predictions` (they read `data/out/`), and the **docsite** (`mkdocs build`) an **independent**
  final asset — it depends on source *docstrings*, not the data, so it carries no upstream data edge
  but rebuilds in the same `dagster dev` run. One orchestrated run then regenerates every code+data
  artifact with per-step status in the UI; the docsite stays dynamic (docstrings re-read each build).
- [ ] **Dagster run logging -> `logs/`.** The `.py` scripts already log to `logs/extract.log` /
  `logs/referral_pathway.log`; add a loguru sink (or use Dagster's event log) for the
  orchestration-level events + the `quarto`/`mkdocs` subprocess output (asset start/success/fail) to
  a `logs/pipeline.log`, so the whole orchestrated run is auditable in one place. Also **set
  `DAGSTER_HOME`** so run history persists (temp dir by default), and **log the resolved
  `config.json`** at load for parity with the auto-logged `.env`.
- [ ] **Migrate to the `dg` CLI (`dg dev`).** `dagster dev -f src/pipeline.py` emits a
  `SupersessionWarning` ("use dg dev instead") on 1.13.x — still fully functional (latest **1.13.10**,
  Jun 2026, per the GitHub releases API), just discouraged. Adopting `dg` means `uv add
  dagster-dg-cli`, a `[tool.dg.project]` block in `pyproject.toml` (root module), and the dg
  project/Components layout — a tooling modernization deferred so the MVP stays minimal. Docs:
  https://docs.dagster.io/guides/labs/dg/configuring-dg.
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

- [ ] **`README.qmd` business answers.** The pipeline should **dynamically generate the plots and
  tables** answering the four PharmaCorp questions and embed them — with the per-case
  `referral_pathway` diagrams — in a **`README.qmd`** rendered to **GitHub-flavoured markdown** via
  `quarto render` (CLI). Gives a static, version-controlled answers doc that refreshes from the
  latest predictions.
- [ ] **System-design diagram — the FINAL large build task.** Rename `docs/DESIGN.qmd` →
  **`docs/SYSTEM_DESIGN.qmd`** and turn its draft into the **simplest possible** Quarto **Mermaid**
  chart of the real workflow, whose job is to clarify the **Dagster / `uv run` relation**:
  `dagster dev -f src/pipeline.py` is the orchestrating entry point, while `uv run python
  src/main.py` (CLI) and the `.sh` gate run the *same* `src/` functions **standalone** (library-first,
  not nested); static `data/in/interviews.json` input → no sensor; the gate surfaced as asset checks.
  **Do this last**, once Dagster actually runs, so the diagram matches the built workflow — then
  **link it from `README.qmd`** (there is no link today). While here, fix the draft's stale bits:
  title `Chronicity` → `Crohnicity`, `_v3.ods` → `_v5.ods`, and the `main.py`-as-orchestrator flow →
  the Dagster asset graph. Render with `quarto render docs/SYSTEM_DESIGN.qmd`.

## Packaging — Docker

- [ ] After the `src/` refactor, add the **simplest possible Dockerfile** producing the **smallest
  image** for this use case (e.g. `python:3.14-slim` + `uv sync --frozen`), so the whole pipeline can
  be built, run and tested **on any machine** independently of the local environment — the
  cross-machine reproducibility check (does it run off my laptop?).

## Final clean-up sweep — before the final build

The last pass before finalising, **after** the pipeline runs end-to-end. Do **all** of:

- [ ] **Centralise config in a `config.json`.** Every setting used by *any* script
  (`.py`/`.qmd`/`.sh`) reads from one file: model-name defaults, the gold dataset path + version
  (`_v5.ods`), the source `data/in/interviews.json` path, the `data/out/` location, chunk size, etc.
  No hard-coded paths/params scattered across `extract.py` / `main.py` / `post_extraction_eda.py` /
  `referral_pathway_analysis.py` / `README.qmd` — a single source of truth that all files load.
- [ ] **Kill redundancy + fix drift.** Redundant code/docs and drifted definitions/docstrings —
  e.g. the mkdocs nav says "Schema (v0.2)" while `SCHEMA.md` is v0.4; stale `_v3.ods`/`_v4.ods`
  mentions; the `DESIGN.qmd` draft's `_v3.ods` + `main.py`-as-orchestrator flow; duplicated setup text.
- [ ] **Every TODO item addressed** (this file) — each one done, or consciously moved to
  README → *Next Steps* as post-MVP.
- [ ] **Every question answered** — cross-check `docs/TASK_INSTRUCTIONS.md` *and* `README.qmd`: all
  four business questions *and* the schema / pipeline / evaluation dev-questions carry a written
  answer (no prompt-only sections left). This is the last gate before CAIO handover.
- [ ] **Docsite builds complete.** `uv run mkdocs build` covers *all* `src/` modules + tests via
  mkdocstrings — done (`api/src.md` + `api/tests.md` cover all 8 src modules + tests); remaining:
  keep nav labels current (e.g. "Schema (v0.2)" -> v0.4).
- [ ] **Review `src/splits.py`'s place in the pipeline.** The validation/holdout split derives from
  the `to_review` flag, but the eval now reads the gold directly (`gold_eval` filters
  `to_review == 1` itself) and only 20/50 cases are annotated — so `splits.py` may be redundant now.
  Check whether anything still imports it; if not, **move `splits.py` + `test_splits.py` to
  `sandbox/`** (with the other once-used/adhoc scripts, kept as a dev-documentation record) rather
  than deleting — and drop their `api/src.md` / `api/tests.md` entries so the docsite still builds.
- [ ] **EDA plot clarity + correctness (diagnosed; fix in final sweep).**
  - **Q2 `(null)` -> `unspecified`** — relabelled in `q2_reasons`, but it masks a real gap: the model
    left `reasons_for_biologic_not_taken` null for the 2 prescribed-not-taken cases (**P047, P048**).
    Prompt fix: always set a `ReasonNotTaken` (default `UNKNOWN`); re-run extraction to take effect.
  - **Q3 "treatments before a biologic" includes biologics** — the `biologic` bar (2) = **P043** (a
    genuine switch: Remicade FAILED -> Humira) + **P046** (the *taken* biologic Humira mislabelled
    `before_biologic=True`). Clarify whether Q3 counts earlier/switched biologics or only non-biologic
    treatments; fix the plot title/definition + the P046 mislabel (prompt). Also clarify on the plot
    whether "treatments" includes biologics.
  - **Q4 `q4_steps.png`** — annotate with **N** (cohort size, n=50) so the population is visible on the plot.

- [ ] **Security check before handover.** Confirm the GitHub repo is **private**
  (`gh repo view --json visibility`) and the **`.gitignore` is correct** — `.env` (the only secret,
  `GEMINI_API_KEY`), `.venv/`, `site/`, and the Dagster run-state (`logs/dagster/*` except
  `dagster.yaml`) are all ignored, and `git ls-files` lists no credentials or unintended files. The
  synthetic `data/in` / `data/out` are committed *deliberately* — see README → *Data handling & privacy*.

## Polish

- [ ] **Duplicate title in the pathway graphs / MkDocs** — the per-case graph heading renders
  twice (e.g. `Referral pathway: P005` / `Referral pathway: P005`), likely the pyvis `heading`
  argument doubling up. De-duplicate in `src/referral_pathway_analysis.py` (`render`) and check
  the docs page.
