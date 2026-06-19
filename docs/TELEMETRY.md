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
