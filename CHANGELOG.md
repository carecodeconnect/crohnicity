# Changelog

Notable changes to the Crohnicity **pipeline**, for vetting across runs.

> **Current values** (model, paths, gold/app versions, ports, decoding params) are the single source
> of truth in [`config.json`](config.json) / [`pyproject.toml`](pyproject.toml) — this file records
> *changes* over time (naming old→new is correct here: it's history, not a live pointer).
> **Schema-vocabulary** history lives in [`docs/SCHEMA.md`](docs/SCHEMA.md#changelog).

## [0.1.0] — 2026-06-29

### Model & inference
- **Extraction model `gemini-2.5-flash-lite` → `gemini-2.5-flash`.** Rode past `-lite`'s sustained
  503 "high demand" spikes (free-tier quota is per-model, so `-flash` has its own pool) and gave the
  batched JSON enough output budget.
- **Disabled model reasoning** (`reasoning_effort="disable"` → `thinkingBudget=0`). Extraction is
  classification, not multi-step inference: the hidden thinking step added run-to-run variance and,
  on `-flash`, consumed the token budget until the JSON truncated mid-array. Off = deterministic, no
  truncation, cheaper/faster. (Explicit, *inspectable* chain-of-thought is deferred to the multi-stage
  Next Step — a different thing from opaque internal tokens.)
- **`max_tokens` 8192 → 32768** — headroom for a 10-patient batch.

### Reliability / error handling
- **`give_up_reason()`** encodes the stop-vs-retry decision in code (not manual log-watching):
  **429** = stop (the quota won't clear by retrying), **503** = transient overload, retried
  `retry_503_max`× `retry_503_delay_s`s apart, then give up.
- **`run_chunked` skips + logs** a chunk whose output is invalid/truncated
  (`JSONSchemaValidationError` / Pydantic `ValidationError`) and continues — one bad chunk no longer
  aborts the whole run; 429/503 still stop it.

### Pipeline / orchestration
- **Added the `referral_pathways_md` Dagster asset** (`deps=[predictions]`; renders
  `docs/referral_pathways.qmd`) and made **`docsite` depend on it**, so the journey gallery is rebuilt
  from the latest predictions before the site is built. Previously `docsite` was independent and could
  ship a stale committed gallery.

### Reproducibility / docs
- Centralised current values in `config.json` / `pyproject.toml`; the README renders them dynamically
  (version · model · gold) and docs **link to the SSOT** rather than restating literals.
- **`docs/TELEMETRY.md` brought current**: model references point to the `config.json` SSOT (no stale
  `-lite` as "current"; the measured-diagnostics table is framed as `-lite` iteration history),
  reasoning is documented as disabled (no thinking/reasoning tokens to account for), and the
  ModelResponse/RAW-RESPONSE reading guidance now matches the actual `telemetry: ...` line in
  `extract.py` (`model temperature prompt/completion/total tokens cost_usd`).

### Quality (this run)
- **churn detection improved** with `-flash` + reasoning off: it now flags the previously-missed
  truncation case **P049** — zero false negatives on the reviewed gold churn set this run.
- Q1 (headline): **74% (37/50)** appear to be on a biologic.
