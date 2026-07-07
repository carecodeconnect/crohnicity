"""Minimal LiteLLM/Gemini extraction: one interview transcript -> PatientLabels (a prediction).

Builds on the canonical call verified in `notebooks/00_setup.ipynb` (litellm.completion,
a Gemini model, GEMINI_API_KEY loaded from `.env`) and the documented Gemini
structured-output pattern (https://docs.litellm.ai/docs/providers/gemini):

    response_format={"type": "json_object", "response_schema": <json schema>,
                     "enforce_validation": True}

We pass `PatientLabels.model_json_schema()` as `response_schema`, so Pydantic builds the schema
(accurate for our nested models), Gemini is constrained to it, and `enforce_validation` makes
LiteLLM validate the reply — raising `litellm.JSONSchemaValidationError` on a bad output.
`model_validate_json(...)` then materialises the typed object.

The MVP includes a *simple* referral_pathway instruction (in the prompt below); refining the
step vocabulary / journey-type clustering is the big post-MVP task (docs/TODO.md).

TO VERIFY in testing (see docs/RESOURCES.md): whether Gemini 2.5 accepts the `$defs`/`$ref`
Pydantic emits for the nested models, and whether the LiteLLM path matches the OpenAI-SDK path.
"""

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import litellm
from dotenv import load_dotenv
from loguru import logger

from config import (
    JSON_DIR,
    LOG_DIR,
    MAX_TOKENS,
    MODEL,
    OUT_DIR,
    PROMPT,
    RETRY_503_DELAY_S,
    RETRY_503_MAX,
    TEMPERATURE,
)
from schema import BatchPredictions, Interview, PatientLabels

T = TypeVar("T")

# API errors we log cleanly and surface for a graceful CLI exit (no traceback dump):
# 429 (rate limit), 503 (busy), connection / model-not-found, and schema mismatch.
HANDLED = (
    litellm.AuthenticationError,
    litellm.RateLimitError,
    litellm.ServiceUnavailableError,
    litellm.APIConnectionError,
    litellm.JSONSchemaValidationError,
)
TESTS_OUT = (
    OUT_DIR / "tests"
)  # synthetic/test outputs, not production (OUT_DIR from config)

# loguru file sink: persist each run + failures (stderr stays on by default)
logger.add(
    LOG_DIR / "extract.log",
    level="INFO",
    rotation="1 MB",
    filter=lambda r: r["name"] == "extract",  # keep this sink to extract.py's own logs
)

# Prompt lives in data/prompts/system.txt (PROMPT in config) — a reviewable artifact.
SYSTEM_PROMPT = PROMPT.read_text().strip()
# the schema sent to the model on every call
RESPONSE_SCHEMA = PatientLabels.model_json_schema()

# the static prompt + schema are logged once per run, not per call
_request_config_logged = False


def _log_request_config() -> None:
    """Log the system prompt + Pydantic schema once per process (file I/O only — no API cost), so
    every run records the static model input; the per-call user message + output go in extract()."""
    global _request_config_logged
    if not _request_config_logged:
        logger.info("system prompt sent to model:\n{}", SYSTEM_PROMPT)
        logger.info("response schema sent to model: {}", json.dumps(RESPONSE_SCHEMA))
        _request_config_logged = True


def _with_503_retry(call: Callable[[], T]) -> T:
    """Run a Gemini call with quota-aware retry. litellm's own retries are OFF (``num_retries=0`` at
    the call site) so one failure costs ONE request, not three — on the free-tier daily cap a failed
    request is as expensive as a successful one. ONLY 503 (``ServiceUnavailableError``, transient
    overload) is retried, sparingly: up to ``RETRY_503_MAX`` times with a long ``RETRY_503_DELAY_S``
    gap. Rate limits (429) and every other error are NOT retried — they fail fast so the daily quota
    isn't spent on attempts that can't succeed."""
    for attempt in range(RETRY_503_MAX + 1):
        try:
            return call()
        except litellm.ServiceUnavailableError:
            if attempt == RETRY_503_MAX:
                raise
            logger.warning(
                "503 ServiceUnavailable (attempt {}/{}) — sleeping {}s before retry",
                attempt + 1,
                RETRY_503_MAX + 1,
                RETRY_503_DELAY_S,
            )
            time.sleep(RETRY_503_DELAY_S)
    raise AssertionError("unreachable")  # loop always returns or raises


def give_up_reason(e: Exception) -> str:
    """The action to take for a terminal API/schema error — the 429-stop vs 503-retry decision lives
    here in code, not in the operator's head: 429 = STOP (the quota won't clear by retrying); 503 =
    transient overload, wait and re-run."""
    if isinstance(e, litellm.AuthenticationError):
        return (
            "401 invalid credentials — NOT retried; fix GEMINI_API_KEY in .env "
            "(mint a key at https://aistudio.google.com/apikey)"
        )
    if isinstance(e, litellm.RateLimitError):
        return "429 rate/daily quota — NOT retried; STOP, re-running won't help until the quota resets"
    if isinstance(e, litellm.ServiceUnavailableError):
        return f"503 transient overload — retried {RETRY_503_MAX}x then gave up; wait and re-run later"
    if isinstance(e, litellm.APIConnectionError):
        return "connection error — check the model name / `ollama serve` / network"
    if isinstance(e, litellm.JSONSchemaValidationError):
        return "schema mismatch — try a more capable model"
    return f"{type(e).__name__} — see logs/"


# Log unexpected failures (traceback) + re-raise; retryable API errors handled below.
@logger.catch(exclude=HANDLED, reraise=True)
def extract(
    transcript: str, patient_id: str, out_dir: Path = JSON_DIR, model: str = MODEL
) -> PatientLabels:
    """Extract one patient's labels from their interview transcript via Gemini (a prediction)."""
    load_dotenv()  # GEMINI_API_KEY -> env; litellm reads it for the gemini/ provider
    _log_request_config()  # once per run: the system prompt + schema sent to the model
    user_message = f"patient_id: {patient_id}\n\n{transcript}"
    logger.info("{} input: {}", patient_id, user_message)  # logged before the call
    try:
        response = _with_503_retry(
            lambda: litellm.completion(
                model=model,
                num_retries=0,  # we own retries: 503 only, sparingly (see _with_503_retry)
                temperature=TEMPERATURE,  # 0 = deterministic; logged below for cross-run comparison
                reasoning_effort="disable",  # extraction is classification, not multi-step reasoning (-> thinkingBudget=0)
                # drop params a provider doesn't support (Gemini vs Ollama)
                drop_params=True,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={
                    "type": "json_object",
                    "response_schema": RESPONSE_SCHEMA,
                    "enforce_validation": True,
                },
            )
        )
    except HANDLED as e:
        # expected API/schema error (litellm already retried) — on a schema rejection, log the
        # model's raw output so we can see what it returned; then re-raise.
        raw = getattr(e, "raw_response", None)
        if raw:
            logger.error("{} rejected raw response: {}", patient_id, raw)
        logger.error("{}: {}", patient_id, give_up_reason(e))
        raise
    # Telemetry: token usage + cost per call, persisted for cost/latency EDA without re-running.
    logger.info(
        "{} telemetry: model={} temperature={} prompt_tokens={} completion_tokens={} total_tokens={} cost_usd={}",
        patient_id,
        model,
        TEMPERATURE,
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
        response.usage.total_tokens,
        getattr(response, "_hidden_params", {}).get("response_cost"),
    )
    # Raw model output BEFORE validation — so a schema failure can be diagnosed from the log.
    raw = response.choices[0].message.content
    logger.info("{} raw model response: {}", patient_id, raw)
    labels = PatientLabels.model_validate_json(raw)
    path = save(labels, out_dir)
    logger.info("{} output (validated): {}", patient_id, labels.model_dump_json())
    logger.info("extracted {} -> {}", patient_id, path)
    return labels


def save(labels: PatientLabels, out_dir: Path = JSON_DIR) -> Path:
    """Write the prediction to ``<out_dir>/<patient_id>.json`` and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{labels.patient_id}.json"
    path.write_text(labels.model_dump_json(indent=2))
    return path


# Appended to SYSTEM_PROMPT for chunked calls (several interviews in one request).
BATCH_SUFFIX = (
    " You are given several interviews, each prefixed with its patient_id and separated by '---'. "
    "Return one prediction per patient in `predictions`, copying each patient_id exactly."
)


@logger.catch(exclude=HANDLED, reraise=True)
def extract_batch(
    interviews: list[Interview], out_dir: Path = JSON_DIR, model: str = MODEL
) -> list[PatientLabels]:
    """Extract a chunk of interviews in ONE call — fewer requests for the daily cap (see main.py
    `--chunk-size`). A malformed/truncated batch raises (enforce_validation); `run_chunked`
    (main.py) skips + logs that chunk and continues — per-record salvage is future hardening
    (docs/TODO.md)."""
    load_dotenv()  # GEMINI_API_KEY -> env
    ids = [r.patient_id for r in interviews]
    user_message = "\n\n---\n\n".join(
        f"patient_id: {r.patient_id}\n\n{r.interview_transcript}" for r in interviews
    )
    logger.info("batch input ({} patients): {}", len(ids), ids)
    try:
        response = _with_503_retry(
            lambda: litellm.completion(
                model=model,
                num_retries=0,  # we own retries: 503 only, sparingly (see _with_503_retry)
                temperature=TEMPERATURE,  # 0 = deterministic; logged below for cross-run comparison
                reasoning_effort="disable",  # classification task; frees the token budget for JSON (-> thinkingBudget=0)
                drop_params=True,
                max_tokens=MAX_TOKENS,  # headroom for ~N records (keep chunk_size <= ~15)
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT + BATCH_SUFFIX},
                    {"role": "user", "content": user_message},
                ],
                response_format={
                    "type": "json_object",
                    "response_schema": BatchPredictions.model_json_schema(),
                    "enforce_validation": True,
                },
            )
        )
    except HANDLED as e:
        raw_err = getattr(e, "raw_response", None)
        if raw_err:
            logger.error("batch {} rejected raw response: {}", ids, raw_err)
        logger.error("batch {}: {}", ids, give_up_reason(e))
        raise
    logger.info(
        "batch telemetry: model={} temperature={} patients={} total_tokens={} cost_usd={}",
        model,
        TEMPERATURE,
        len(ids),
        response.usage.total_tokens,
        getattr(response, "_hidden_params", {}).get("response_cost"),
    )
    raw = response.choices[0].message.content
    logger.info("batch raw response: {}", raw)
    labels = BatchPredictions.model_validate_json(raw).predictions
    for x in labels:
        logger.info("extracted {} -> {}", x.patient_id, save(x, out_dir))
    return labels
