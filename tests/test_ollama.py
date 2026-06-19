"""Live Ollama tests — gated by RUN_OLLAMA_TESTS=1 (needs `ollama serve` + the model pulled).

Checks the local-model path: (1) server reachable, (2) model available, (3) extract() returns a
schema-valid PatientLabels. Set OLLAMA_MODEL (default `ollama_chat/gemma4`). A small model often
fails (3) by inventing its own fields — that failure is the useful signal that you need a
larger/instruction-tuned model for schema/API compatibility.
"""

import os

import httpx
import pytest

from extract import extract
from schema import PatientLabels

OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama_chat/gemma4")
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
    assert httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5).status_code == 200


def test_ollama_model_available() -> None:
    """The configured model has been pulled into Ollama."""
    _require_ollama()
    models = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5).json().get("models", [])
    names = [m.get("name", "") for m in models]
    short = OLLAMA_MODEL.split("/")[-1]
    assert any(short in n for n in names), f"{short} not pulled; have {names}"


def test_ollama_extract_schema(tmp_path) -> None:
    """extract() with the local model returns a schema-valid PatientLabels (may fail on small models)."""
    _require_ollama()
    result = extract(SYNTHETIC, "P000", out_dir=tmp_path, model=OLLAMA_MODEL)
    assert isinstance(result, PatientLabels)
    assert result.patient_id == "P000"
