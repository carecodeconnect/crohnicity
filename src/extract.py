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

from pathlib import Path

import litellm
from dotenv import load_dotenv
from loguru import logger

from schema import PatientLabels

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


# Log unexpected failures (traceback) + re-raise; retryable API errors handled below.
@logger.catch(exclude=HANDLED, reraise=True)
def extract(
    transcript: str, patient_id: str, out_dir: Path = OUT_DIR, model: str = MODEL
) -> PatientLabels:
    """Extract one patient's labels from their interview transcript via Gemini (a prediction)."""
    load_dotenv()  # GEMINI_API_KEY -> env; litellm reads it for the gemini/ provider
    try:
        response = litellm.completion(
            model=model,
            num_retries=MAX_RETRIES,
            # drop params a provider doesn't support (Gemini vs Ollama)
            drop_params=True,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"patient_id: {patient_id}\n\n{transcript}",
                },
            ],
            response_format={
                "type": "json_object",
                "response_schema": PatientLabels.model_json_schema(),
                "enforce_validation": True,
            },
        )
    except HANDLED as e:
        # expected API/schema error (litellm already retried) — clean line, no stack dump.
        logger.error("{} for {} — gave up after retries", type(e).__name__, patient_id)
        raise
    labels = PatientLabels.model_validate_json(response.choices[0].message.content)
    path = save(labels, out_dir)
    logger.info("extracted {} -> {}", patient_id, path)
    return labels


def save(labels: PatientLabels, out_dir: Path = OUT_DIR) -> Path:
    """Write the prediction to ``<out_dir>/<patient_id>.json`` and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{labels.patient_id}.json"
    path.write_text(labels.model_dump_json(indent=2))
    return path
