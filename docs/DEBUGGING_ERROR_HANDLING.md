# Debugging & error handling

How we **trace** the LiteLLM/Gemini calls and **handle** what goes wrong. This is **distinct from
schema / data validation** (field types, enums, null semantics) — that lives in
[`SCHEMA.md`](SCHEMA.md). Here we cover the debug output and the exceptions around the
`litellm.completion(...)` call.

Principle: **surface failures, never swallow them.** loguru's `@logger.catch(reraise=True)` on
`extract()` logs any *unexpected* error (with traceback) to `logs/extract.log` and re-raises;
the specific cases below get cleaner, targeted handling.

## Debugging — LiteLLM verbose output

`litellm._turn_on_debug()` (enabled in `notebooks/03_extraction_test`) makes LiteLLM log the full
call through the stdlib `LiteLLM` logger; a file handler on that logger persists it to
`logs/litellm_debug.log` — separate from loguru's `logs/extract.log` (different logging systems).
What it captures, and why it's handy:

- The **`curl` request** LiteLLM sends to `generativelanguage.googleapis.com` — copy/paste it to
  replay the exact call from the shell and debug it outside the pipeline. The API key is redacted
  (`x-goog-REDACTED`), so the line is safe to share.
- The **raw JSON response** (pre-parsing), the **token counts** (`usageMetadata`, incl. cached
  tokens), and the computed **`response_cost`** — useful for cost/latency tuning later.

> Note: the debug request embeds the **prompt + transcript text**. Fine for the synthetic data,
> but for *real* patient transcripts that's the PII concern in [`QUESTIONS.md`](QUESTIONS.md) #7 —
> don't commit debug logs of real data.

## Errors handled now

| Error | When | Handling | Where |
|-------|------|----------|-------|
| `ServiceUnavailableError` (**503**) | model busy / transient overload | `_with_503_retry` retries **sparingly** — `RETRY_503_MAX` attempts, `RETRY_503_DELAY_S` apart (both set in `config.json`) — then a concise `ERROR` line (no stack dump — `excluded` from `@logger.catch`) and re-raise. litellm's own retries are OFF (`num_retries=0`). | `src/extract.py` |
| `RateLimitError` (**429**) | rate-limit / daily quota | **NOT retried — fails fast.** On the free tier a failed request costs the same daily quota as a successful one, so retrying a quota error just burns more of it. Concise `ERROR` line, then re-raised. | `src/extract.py` |
| `AuthenticationError` (**401**) | missing/invalid/rotated `GEMINI_API_KEY` | **NOT retried — fails fast.** No amount of retrying fixes a bad credential; the message says to fix the key in `.env` (mint one at <https://aistudio.google.com/apikey>). Surfaced live when the key was rotated on going public. | `src/extract.py` |
| 429 (or exhausted 503) reaching the CLI | quota hit, or 503 retries used up | `main()` catches it and **exits gracefully** — a clean one-liner with the rate-limits URL, exit 1, no traceback (fail-fast) | `src/main.py` |
| `JSONSchemaValidationError` / Pydantic `ValidationError` | output invalid/truncated (e.g. a reasoning model exhausts `max_tokens` before finishing the JSON) | **Skip that chunk + log, continue the run** — one bad chunk can't abort the whole extraction; skipped `patient_id`s are counted + logged. `enforce_validation` raises this *inside* `litellm.completion`. | `src/main.py` (`run_chunked`) |

## Planned (see [`TODO.md`](TODO.md) → Robustness)

The skip-vs-fail-fast *policy* is now implemented (schema-validation → skip the chunk; 429/503 →
fail-fast). Still future hardening: per-**record** salvage from a partially-valid batch (today the
whole chunk is skipped, not just the one bad record), and finer malformed-JSON / empty-response
sub-cases.

## Reference

- **LiteLLM exception mapping** — status code → exception class (all subclass the OpenAI SDK
  exceptions): <https://docs.litellm.ai/docs/exception_mapping>
  - `503 → ServiceUnavailableError`, `429 → RateLimitError`, `400 → BadRequestError`,
    `408 → Timeout`, `401 → AuthenticationError`, `≥500 → APIError` / `InternalServerError`.
  - Exceptions carry `status_code`, `message`, `llm_provider`; `litellm._should_retry(status_code)`
    helps decide retries.
- **LiteLLM Gemini provider** (our path): <https://docs.litellm.ai/docs/providers/gemini>
