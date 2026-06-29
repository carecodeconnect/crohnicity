# API-call telemetry

What each LiteLLM/Gemini call exposes for **cost/latency optimisation and scaling EDA**, and how to
read it. Captured here as findings for when we build the metrics capture + plots (tracked in
[`TODO.md`](TODO.md) → *Metrics & EDA*). For the verbose debug *stream* and error handling, see
[`DEBUGGING_ERROR_HANDLING.md`](DEBUGGING_ERROR_HANDLING.md).

## What's available, per call

Token usage (prompt / completion / total), **cached** tokens, **cost** (USD), latency, plus
`finish_reason`, `model_version`, `service_tier`, `response_id`. **Reasoning is disabled** for this
pipeline (`reasoning_effort="disable"` → `thinkingBudget=0` in [`extract.py`](../src/extract.py)), so
there are **no thinking/reasoning tokens to account for** — `completion_tokens` is the JSON output
only, not output + hidden thinking.

The model and decoding params (model string, `temperature`) are the SSOT in
[`config.json`](../config.json), not restated here.

## What `extract()` actually logs (`telemetry: ...` in `logs/extract.log`)

Per call, `extract.py` logs exactly these fields (keep any EDA capture in sync with this line):

```
model temperature prompt_tokens completion_tokens total_tokens cost_usd
```

`extract_batch()` logs the same minus the per-record split (`patients total_tokens cost_usd`). These
are the fields to parse for cost/latency EDA without re-running.

## Source 1 — the LiteLLM `ModelResponse` (preferred: structured, in-process)

`extract()`'s `response = litellm.completion(...)` returns a `ModelResponse`; the telemetry line
above is read straight off it. The full object exposes more than `extract()` logs — read it directly
rather than parsing logs:

```python
u = response.usage                          # litellm.types.utils.Usage
u.prompt_tokens, u.completion_tokens, u.total_tokens   # logged in the telemetry line
u.prompt_tokens_details.cached_tokens       # context-cache hits (not logged)
u.cache_read_input_tokens
response.model                              # the model string (SSOT: config.json) — logged
response.choices[0].finish_reason           # "stop" (not logged)

import litellm
litellm.completion_cost(response)           # USD; or response._hidden_params["response_cost"] (-> cost_usd)
```

`response.model_dump_json()` / `.json()` dumps the whole wrapper — explored in
`notebooks/00_setup.ipynb`; see also [`RESOURCES.md`](RESOURCES.md) (the ModelResponse object).

## Source 2 — the `RAW RESPONSE` in `logs/litellm_debug.log`

With `litellm._turn_on_debug()` on (the notebook), the debug log records Gemini's native response,
including `usageMetadata`:

```json
"usageMetadata": {
  "promptTokenCount": 137,
  "candidatesTokenCount": 372,
  "totalTokenCount": 509,
  "cachedContentTokenCount": 92,
  "serviceTier": "standard"
},
"modelVersion": "<the model from config.json>",
"responseId": "z0M1asv4K4OfvdIPmY2fkA4"
```

followed by a `response_cost: 0.00015302` line. Same numbers as Source 1, but with Gemini's field
names and embedded in verbose text. Use only if the debug stream is already being kept; otherwise
prefer Source 1. With reasoning disabled (`thinkingBudget=0`) there's **no `thoughtsTokenCount`** —
`candidatesTokenCount` is the JSON output alone.

## Field mapping (Gemini-native ↔ LiteLLM)

| Gemini `usageMetadata` | LiteLLM `response.usage` |
|---|---|
| `promptTokenCount` | `prompt_tokens` |
| `candidatesTokenCount` | `completion_tokens` |
| `totalTokenCount` | `total_tokens` |
| `cachedContentTokenCount` | `prompt_tokens_details.cached_tokens` / `cache_read_input_tokens` |

Latency isn't in either payload — derive it from the call (wall-clock around `completion()`, or the
debug log's request/response timestamps).

## Measured diagnostics — iteration runs (`gemini-2.5-flash-lite`), this dataset

> **Historical / iteration history.** These numbers were measured during early iteration on
> `gemini-2.5-flash-lite` — *not* the current model. The live model and decoding params are the SSOT
> in [`config.json`](../config.json) (the run since moved to `gemini-2.5-flash` with reasoning
> disabled). Treat the table below as order-of-magnitude shape, not the figures for the current run;
> for the live run read the per-call `telemetry: ...` lines in `logs/extract.log` (the field list is
> above). Reasoning is now disabled in the live run, so the live `completion_tokens` is JSON output
> only (no thinking tokens) regardless of these historical figures.

From those early single-patient runs (logged in `logs/litellm_debug.log`; `extract.py` also logs a
per-call `telemetry: ...` line to `logs/extract.log`):

| Metric | Per single-patient call |
|---|---|
| `prompt_tokens` | ~270 (system prompt + transcript; **the `response_schema` is not billed as prompt tokens**) |
| `completion_tokens` | ~400 (the JSON record) |
| `total_tokens` | ~670 |
| `cached_tokens` | ~90 (context-cache hit on the static system prompt) |
| cost | ~$0.00019 / call → **~$0.01 for all 50** |

**Free-tier rate limits observed (the binding constraints, not tokens):**

| Limit | Value | Implication |
|---|---|---|
| **Requests/day (RPD)** | **20** (from the 429: `generate_content_free_tier_requests, limit: 20`) | **50 individual calls can't finish in one free-tier day** — the real blocker |
| Tokens/min (TPM) | 250,000 | irrelevant at ~670 tok/call |
| Requests/min (RPM) | ~10–15 | fine for sequential calls |

**Takeaways for optimisation/diagnosis:**

- Cost/tokens are *not* the constraint — **request count (20/day) is**. Optimise for fewer requests
  (chunking N patients/call — `chunk_size` in [`config.json`](../config.json)), not fewer tokens. A
  10-patient chunk ≈ 4.9K tokens, well within TPM, output well under the `max_tokens` cap (config
  SSOT) → **10×5 = 5 requests** fits the daily cap.
- The system prompt is **context-cached** (~90 tokens cached/call) — keeping it stable across calls
  preserves the cache hit.
- **Local Ollama**: `response.usage` still populates (litellm normalises it), but `cost_usd` is
  `None`/0 (no billing) — so cost EDA only applies to the Gemini path.
