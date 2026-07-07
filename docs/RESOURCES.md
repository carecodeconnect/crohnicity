# Resources

References for the tricky parts of the pipeline — chiefly **how LiteLLM uses and validates the
Pydantic schema with Gemini** (structured output) and what the `ModelResponse` carries. To check
against during testing, not to assume.

## LiteLLM + Gemini structured output / Pydantic validation

- [Structured outputs with Gemini via LiteLLM does not work](https://github.com/openai/openai-agents-python/issues/1575)
  — the flagged issue: how a Pydantic schema validates a LiteLLM `ModelResponse`, and that it can
  break with Gemini.
- [fix(gemini): preserve `$ref` in JSON Schema for Gemini 2.0+](https://github.com/BerriAI/litellm/pull/21597)
  — **most relevant to us**: Gemini 2.0+ can handle the `$ref`/`$defs` Pydantic emits for our
  nested models after this fix.
- [normalize response_schema on native generateContent](https://github.com/BerriAI/litellm/pull/27775)
- [Google AI generateContent needs a different request body shape](https://github.com/BerriAI/litellm/issues/12671) (open)
- [response_format + web_search returns raw tool tokens, not parsed JSON](https://github.com/BerriAI/litellm/issues/17556)
- Nested-Pydantic conversion issues: [#6027](https://github.com/BerriAI/litellm/issues/6027),
  [#6830](https://github.com/BerriAI/litellm/issues/6830),
  [#6848](https://github.com/BerriAI/litellm/issues/6848).

## Which Gemini model — does swapping change the call?

- Our model is the single source of truth in [`config.json`](../config.json) (`config.MODEL`); the call pattern was first sanity-checked in `notebooks/00_setup.ipynb`.
- Gemini **2.0+ uses the native `responseJsonSchema`**; LiteLLM maps our `response_format`
  (`response_schema` + `enforce_validation`) onto it, preserving the `$ref`/`$defs` Pydantic
  emits for nested models (PR #21597; gemini-3 preview added the same, PR #30696).
- **Swapping models:** staying within Gemini 2.0+ should *not* change our API parameters
  (LiteLLM abstracts the per-model native param). **Double-check when we swap** — especially to a
  different provider, where `response_format` handling can differ.

## The LiteLLM `ModelResponse` object (post-inference)

`litellm.completion(...)` returns a **`ModelResponse`** (itself a Pydantic model). Two layers,
kept distinct:

- `response.choices[0].message.content` — the assistant's content; for our structured call this
  is the JSON we validate into `PatientLabels`. **Schema validation acts on this.**
- `response.model_dump_json()` — JSON of the *whole `ModelResponse` wrapper* (id, choices,
  `usage`, caching, etc.), **not** our schema. Useful for **error handling / cost + token
  optimisation** — the token/cost fields are documented in [`TELEMETRY.md`](TELEMETRY.md).

**Reasoning output:** we **disable** model reasoning for extraction (`reasoning_effort="disable"` →
`thinkingBudget=0`, in [`src/extract.py`](../src/extract.py); rationale in SOLUTION → *Determinism*),
so `reasoning_content` / `thinking_blocks` aren't used here. (Their docs were also inconsistent —
`thinking_blocks` looks Anthropic-only — noted in `00_setup.ipynb`.)

---

<sub>**Footnote — OpenAI SDK vs LiteLLM SDK:** `response_format` / structured-output behaviour can
differ between the two SDKs (and Gemini-native vs OpenAI-compatible paths). Not central here — we
use the LiteLLM SDK with the documented Gemini pattern — noted for completeness. LiteLLM Gemini
provider doc (ground truth): https://docs.litellm.ai/docs/providers/gemini</sub>
