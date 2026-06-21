"""Minimal LiteLLM/Gemini extraction: one interview transcript -> PatientLabels (a prediction).

Builds on the canonical call verified in `notebooks/00_setup.ipynb` (litellm.completion,
gemini-2.5-flash-lite, GEMINI_API_KEY loaded from `.env`) and the documented Gemini
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
from pathlib import Path

import litellm
from dotenv import load_dotenv
from loguru import logger

from schema import BatchPredictions, Interview, PatientLabels

MODEL = "gemini/gemini-2.5-flash-lite"
MAX_RETRIES = 2  # litellm retries transient 429/503 errors, with backoff
# API errors we log cleanly and surface for a graceful CLI exit (no traceback dump):
# 429 (rate limit), 503 (busy), connection / model-not-found, and schema mismatch.
HANDLED = (
    litellm.RateLimitError,
    litellm.ServiceUnavailableError,
    litellm.APIConnectionError,
    litellm.JSONSchemaValidationError,
)
# Anchor paths to the repo root via __file__, so they hold regardless of caller's cwd
# (e.g. the notebook runs from notebooks/, not the repo root).
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "out"  # predictions
TESTS_OUT = OUT_DIR / "tests"  # synthetic/test outputs, not production
LOG_DIR = ROOT / "logs"  # logs live at the project root, separate from data outputs

# loguru file sink: persist each run + failures (stderr stays on by default)
logger.add(LOG_DIR / "extract.log", level="INFO", rotation="1 MB")

# Prompt lives in data/prompts/system.txt so it can be edited/reviewed as its own artifact.
SYSTEM_PROMPT = (ROOT / "data" / "prompts" / "system.txt").read_text().strip()
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


# Log unexpected failures (traceback) + re-raise; retryable API errors handled below.
@logger.catch(exclude=HANDLED, reraise=True)
def extract(
    transcript: str, patient_id: str, out_dir: Path = OUT_DIR, model: str = MODEL
) -> PatientLabels:
    """Extract one patient's labels from their interview transcript via Gemini (a prediction)."""
    load_dotenv()  # GEMINI_API_KEY -> env; litellm reads it for the gemini/ provider
    _log_request_config()  # once per run: the system prompt + schema sent to the model
    user_message = f"patient_id: {patient_id}\n\n{transcript}"
    logger.info("{} input: {}", patient_id, user_message)  # logged before the call
    try:
        response = litellm.completion(
            model=model,
            num_retries=MAX_RETRIES,
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
    except HANDLED as e:
        # expected API/schema error (litellm already retried) — on a schema rejection, log the
        # model's raw output so we can see what it returned; then re-raise.
        raw = getattr(e, "raw_response", None)
        if raw:
            logger.error("{} rejected raw response: {}", patient_id, raw)
        logger.error("{} for {} — gave up after retries", type(e).__name__, patient_id)
        raise
    # Telemetry: token usage + cost per call, persisted for cost/latency EDA without re-running.
    logger.info(
        "{} telemetry: prompt_tokens={} completion_tokens={} total_tokens={} cost_usd={}",
        patient_id,
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


def save(labels: PatientLabels, out_dir: Path = OUT_DIR) -> Path:
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
    interviews: list[Interview], out_dir: Path = OUT_DIR, model: str = MODEL
) -> list[PatientLabels]:
    """Extract a chunk of interviews in ONE call — fewer requests for the daily cap (see main.py
    `--chunk-size`). Strict: a malformed/short batch fails the whole chunk (minimal; a tolerant
    per-record parse is future hardening — docs/TODO.md)."""
    load_dotenv()  # GEMINI_API_KEY -> env
    ids = [r.patient_id for r in interviews]
    user_message = "\n\n---\n\n".join(
        f"patient_id: {r.patient_id}\n\n{r.interview_transcript}" for r in interviews
    )
    logger.info("batch input ({} patients): {}", len(ids), ids)
    try:
        response = litellm.completion(
            model=model,
            num_retries=MAX_RETRIES,
            drop_params=True,
            max_tokens=8192,  # headroom for ~N records (keep chunk_size <= ~15)
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
    except HANDLED as e:
        raw_err = getattr(e, "raw_response", None)
        if raw_err:
            logger.error("batch {} rejected raw response: {}", ids, raw_err)
        logger.error("{} for batch {} — gave up after retries", type(e).__name__, ids)
        raise
    logger.info(
        "batch telemetry: patients={} total_tokens={} cost_usd={}",
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
