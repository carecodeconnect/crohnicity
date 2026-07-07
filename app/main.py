"""FastAPI service — the single-transcript RESTful front door over the extraction library.

    uv run python app/main.py                      # serve on config.json -> api_port
    uv run uvicorn app.main:app --reload           # dev alternative (default port 8000)

The pipeline stays **library-first**: this app imports ``extract()`` from ``src/`` — the same
function the CLI (``src/main.py``) and the Dagster assets (``src/pipeline.py``) drive — and adds
only HTTP concerns: request/response models (the existing Pydantic ``Interview`` in,
``PatientLabels`` out, re-validated by FastAPI at the response boundary), and the error →
status-code mapping, whose messages come from ``give_up_reason()`` so the action stated to an API
client is identical to what the CLI prints and the logs record.

**Stateless by default**: a request does not write ``data/out/`` unless it opts in with
``?persist=true`` (then the prediction lands in ``data/out/json`` exactly like a batch run).
"""

import sys
from pathlib import Path

# The service layer imports the pipeline library from src/ (same pattern as src/pipeline.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import litellm
import uvicorn
from fastapi import FastAPI, HTTPException

from config import API_PORT, APP_VERSION, JSON_DIR, MODEL
from extract import HANDLED, extract, give_up_reason
from schema import Interview, PatientLabels

app = FastAPI(
    title="Crohnicity extraction API",
    version=APP_VERSION,  # SSOT: pyproject.toml via config
    description="Structures one Crohn's patient interview transcript into a validated "
    "PatientLabels record (LiteLLM -> Gemini, schema-enforced).",
)

# HANDLED upstream error -> HTTP status. A bad key is OUR misconfiguration (500, not the client's
# fault); quota/overload propagate with their own semantics (429/503); a connection failure or
# schema-invalid model output is an upstream failure (502 Bad Gateway). Checked in give_up_reason's
# order; the response detail is give_up_reason(e) — the same action the CLI prints.
_STATUS: list[tuple[type[Exception], int]] = [
    (litellm.AuthenticationError, 500),
    (litellm.RateLimitError, 429),
    (litellm.ServiceUnavailableError, 503),
    (litellm.APIConnectionError, 502),
    (litellm.JSONSchemaValidationError, 502),
]


def _status_code(e: Exception) -> int:
    """Map a HANDLED extraction error to its HTTP status (500 if somehow unmapped)."""
    return next((code for exc, code in _STATUS if isinstance(e, exc)), 500)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness for the Docker HEALTHCHECK — reports the app version + configured model."""
    return {"status": "ok", "version": APP_VERSION, "model": MODEL}


@app.get("/schema")
def schema() -> dict:
    """The PatientLabels JSON schema, so clients can validate without reading the repo."""
    return PatientLabels.model_json_schema()


@app.post("/extract", response_model=PatientLabels)
def extract_endpoint(interview: Interview, persist: bool = False) -> PatientLabels:
    """Extract one patient's labels. Stateless unless ``persist=true`` (writes data/out/json)."""
    try:
        return extract(
            interview.interview_transcript,
            interview.patient_id,
            out_dir=JSON_DIR if persist else None,
        )
    except (
        HANDLED
    ) as e:  # taxonomy + action message shared with the CLI (give_up_reason)
        raise HTTPException(
            status_code=_status_code(e), detail=give_up_reason(e)
        ) from e


if __name__ == "__main__":
    # Port from config.json (api_port) — the SSOT; host 0.0.0.0 so the Dockerised service is
    # reachable through the container's published port.
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
