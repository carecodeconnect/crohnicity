"""Live Ollama tests — gated by RUN_OLLAMA_TESTS=1 (needs `ollama serve` + the model pulled).

Checks the local-model path: (1) server reachable, (2) model available, (3) extract() returns a
schema-valid PatientLabels. Set OLLAMA_MODEL (default `ollama_chat/qwen3:30b-a3b`). Local models
often fail (3) by inventing fields / free-text enums — that's handled gracefully (xfail with the
raw output), so the suite reports the model's capability rather than dumping a traceback.
"""

import os

import httpx
import litellm
import pytest

from extract import extract
from schema import PatientLabels

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama_chat/qwen3:30b-a3b")
SYNTHETIC = (
    "I'm Alex, 38, male. Diagnosed with Crohn's four years ago. After mesalamine and prednisone "
    "failed, my gastroenterologist started me on Humira, which keeps me in remission."
)


def _require_ollama() -> None:
    if os.getenv("RUN_OLLAMA_TESTS") != "1":
        pytest.skip("RUN_OLLAMA_TESTS != 1 — local Ollama tests skipped")


def test_ollama_server_running() -> None:
    """Ollama's HTTP API answers on localhost:11434 (i.e. `ollama serve` is up)."""
    _require_ollama()
    try:
        resp = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    except httpx.RequestError as e:
        pytest.skip(f"Ollama not reachable at {OLLAMA_URL} — run `ollama serve`: {e}")
    assert resp.status_code == 200


def test_ollama_model_available() -> None:
    """The configured model has been pulled into Ollama."""
    _require_ollama()
    models = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5).json().get("models", [])
    names = [m.get("name", "") for m in models]
    short = OLLAMA_MODEL.split("/")[-1]
    assert any(short in n for n in names), f"{short} not pulled; have {names}"


def test_ollama_extract_schema(tmp_path) -> None:
    """extract() with the local model should return a schema-valid PatientLabels.

    Graceful handling (no giant traceback): skip if the model is unreachable, xfail with the raw
    output if the model returns schema-invalid JSON — the common local-model failure mode.
    """
    _require_ollama()
    try:
        result = extract(SYNTHETIC, "P000", out_dir=tmp_path, model=OLLAMA_MODEL)
    except litellm.APIConnectionError as e:
        pytest.skip(f"{OLLAMA_MODEL} unreachable / not pulled: {e}")
    except litellm.JSONSchemaValidationError as e:
        raw = (getattr(e, "raw_response", "") or "")[:300]
        pytest.xfail(f"{OLLAMA_MODEL} returned schema-invalid output: {raw}")
    assert isinstance(result, PatientLabels)
    assert result.patient_id == "P000"
