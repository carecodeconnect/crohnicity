# API-call telemetry

What each LiteLLM/Gemini call exposes for **cost/latency optimisation and scaling EDA**, and how to
read it. Captured here as findings for when we build the metrics capture + plots (tracked in
[`TODO.md`](TODO.md) → *Metrics & EDA*). For the verbose debug *stream* and error handling, see
[`DEBUGGING_ERROR_HANDLING.md`](DEBUGGING_ERROR_HANDLING.md).

## What's available, per call

Token usage (prompt / completion / total), **cached** tokens, **cost** (USD), latency, plus
`finish_reason`, `model_version`, `service_tier`, `response_id`.

## Source 1 — the LiteLLM `ModelResponse` (preferred: structured, in-process)

`extract()`'s `response = litellm.completion(...)` returns a `ModelResponse`; read it directly
rather than parsing logs:

```python
u = response.usage                          # litellm.types.utils.Usage
u.prompt_tokens, u.completion_tokens, u.total_tokens
u.prompt_tokens_details.cached_tokens       # context-cache hits
u.cache_read_input_tokens
response.model                              # "gemini-2.5-flash-lite"
response.choices[0].finish_reason           # "stop"

import litellm
litellm.completion_cost(response)           # USD; or response._hidden_params["response_cost"]
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
"modelVersion": "gemini-2.5-flash-lite",
"responseId": "z0M1asv4K4OfvdIPmY2fkA4"
```

followed by a `response_cost: 0.00015302` line. Same numbers as Source 1, but with Gemini's field
names and embedded in verbose text. Use only if the debug stream is already being kept; otherwise
prefer Source 1.

## Field mapping (Gemini-native ↔ LiteLLM)

| Gemini `usageMetadata` | LiteLLM `response.usage` |
|---|---|
| `promptTokenCount` | `prompt_tokens` |
| `candidatesTokenCount` | `completion_tokens` |
| `totalTokenCount` | `total_tokens` |
| `cachedContentTokenCount` | `prompt_tokens_details.cached_tokens` / `cache_read_input_tokens` |

Latency isn't in either payload — derive it from the call (wall-clock around `completion()`, or the
debug log's request/response timestamps).

## Measured diagnostics — `gemini/gemini-2.5-flash-lite`, this dataset

From the live single-patient runs (logged in `logs/litellm_debug.log`; `extract.py` also logs a
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
  (chunking N patients/call), not fewer tokens. A 10-patient chunk ≈ 4.9K tokens, well within TPM,
  output ~4K < the ~8K default cap → **10×5 = 5 requests** fits the daily cap.
- The system prompt is **context-cached** (~90 tokens cached/call) — keeping it stable across calls
  preserves the cache hit.
- **Local Ollama**: `response.usage` still populates (litellm normalises it), but `cost_usd` is
  `None`/0 (no billing) — so cost EDA only applies to the Gemini path.
