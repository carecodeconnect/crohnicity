"""Tests for the extraction pipeline: the Pydantic schema (offline) and the live Gemini call.

The live test resolves the open question — does LiteLLM validate the response against our schema
*in the call* (via `response_schema` + `enforce_validation`) or only when we `model_validate_json`
it? Running it against Gemini shows the real behaviour (see `docs/RESOURCES.md`). Gated by
`RUN_LIVE_TESTS`: unset = FAIL (configure it in `.env`), `0` = skip, `1` = run the live call.
"""

import os

import litellm
import pytest
from dotenv import load_dotenv

from extract import TESTS_OUT, extract, give_up_reason, save
from schema import BatchPredictions, PatientLabels

load_dotenv()  # so a key in .env is available for the live test

# Synthetic transcript with unambiguous facts to assert against (not from the real dataset).
SYNTHETIC = (
    "I'm Alex, 38, male. Diagnosed with Crohn's four years ago. After mesalamine and prednisone "
    "failed, my gastroenterologist started me on Humira, which I've taken ever since and it keeps "
    "me in remission."
)


def test_schema_generates_and_validates():
    """Offline: the schema produces a JSON schema and validates a well-formed record."""
    assert PatientLabels.model_json_schema()["title"] == "PatientLabels"
    record = PatientLabels.model_validate(
        {
            "patient_id": "P000",
            "biologic_prescribed": True,
            "biologic_taken": True,
            "biologic_not_mentioned": False,
            "treatment_outcome": "SUCCESS",
        }
    )
    assert record.patient_id == "P000"
    assert record.biologic_taken is True


def test_save_writes_json(tmp_path):
    """Offline: save() writes <patient_id>.json that round-trips back to the same labels."""
    labels = PatientLabels.model_validate(
        {
            "patient_id": "P000",
            "biologic_prescribed": True,
            "biologic_taken": True,
            "biologic_not_mentioned": False,
            "treatment_outcome": "SUCCESS",
        }
    )
    path = save(labels, tmp_path)
    assert path.name == "P000.json"
    assert PatientLabels.model_validate_json(path.read_text()) == labels


def test_batch_predictions_schema():
    """Offline: BatchPredictions wraps a list of PatientLabels (the chunked-call response shape)."""
    assert "predictions" in BatchPredictions.model_json_schema()["properties"]
    batch = BatchPredictions.model_validate(
        {
            "predictions": [
                {
                    "patient_id": "P000",
                    "biologic_prescribed": True,
                    "biologic_taken": True,
                    "biologic_not_mentioned": False,
                    "treatment_outcome": "SUCCESS",
                }
            ]
        }
    )
    assert len(batch.predictions) == 1
    assert batch.predictions[0].patient_id == "P000"


def test_extract_end_to_end():
    """Live: extract() returns a valid PatientLabels for the synthetic transcript.

    Three-state gate on RUN_LIVE_TESTS: unset -> FAIL (configure it in .env), "0" -> skip,
    "1" -> run the live Gemini call. Also asserts the key actually loaded from .env.
    """
    flag = os.getenv("RUN_LIVE_TESTS")
    if flag is None:
        pytest.fail("RUN_LIVE_TESTS not set — set it in .env (1=run, 0=skip)")
    if flag != "1":
        pytest.skip("RUN_LIVE_TESTS=0 — live Gemini call skipped")
    assert os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY not loaded from .env"
    result = extract(SYNTHETIC, "P000", out_dir=TESTS_OUT)
    assert isinstance(result, PatientLabels)
    assert result.patient_id == "P000"
    assert result.biologic_taken is True


def test_give_up_reason_429_says_stop():
    """Offline: the stop-vs-retry decision is encoded, not manual — a 429 (rate/daily quota) STOPs."""
    msg = give_up_reason(litellm.RateLimitError("rate", "gemini/x", "gemini"))
    assert "429" in msg and "STOP" in msg


def test_give_up_reason_503_says_wait_and_retry():
    """Offline: a 503 (transient overload) is recoverable — the message points to waiting + re-run."""
    msg = give_up_reason(litellm.ServiceUnavailableError("busy", "gemini/x", "gemini"))
    assert "503" in msg and "re-run" in msg
