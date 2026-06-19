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
| `RETRYABLE` = `RateLimitError` (**429**) + `ServiceUnavailableError` (**503**) | rate-limit / quota or model busy | `litellm.completion(num_retries=2)` backs off + retries; on giving up, a concise `ERROR` line (no stack dump — `excluded` from `@logger.catch`), then re-raised | `src/extract.py` |
| `RETRYABLE` reaching the CLI | retries exhausted mid-run | `main()` catches it and **exits gracefully** — a clean one-liner with the rate-limits URL, exit 1, no traceback (fail-fast) | `src/main.py` |

## Planned (see [`TODO.md`](TODO.md) → Robustness)

Malformed JSON, schema-validation failures (`litellm.JSONSchemaValidationError` / Pydantic
`ValidationError`), partial outputs, and empty responses — decide per type whether to **skip the
record and continue** (a single bad transcript) vs **fail-fast** (like the 429/503 above).

## Reference

- **LiteLLM exception mapping** — status code → exception class (all subclass the OpenAI SDK
  exceptions): <https://docs.litellm.ai/docs/exception_mapping>
  - `503 → ServiceUnavailableError`, `429 → RateLimitError`, `400 → BadRequestError`,
    `408 → Timeout`, `401 → AuthenticationError`, `≥500 → APIError` / `InternalServerError`.
  - Exceptions carry `status_code`, `message`, `llm_provider`; `litellm._should_retry(status_code)`
    helps decide retries.
- **LiteLLM Gemini provider** (our path): <https://docs.litellm.ai/docs/providers/gemini>
