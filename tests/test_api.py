"""Contract tests for the FastAPI service (app/main.py) — offline by default.

`extract` is monkeypatched, so these test the *service layer's contract*: request validation
(Pydantic 422), response shape (PatientLabels re-validated by FastAPI), the stateless-vs-persist
routing, and the HANDLED-error -> HTTP-status mapping (whose detail is `give_up_reason(e)` — the
same action message the CLI prints). The real Gemini call is covered by the live-gated test in
test_extract.py; no API key or network is needed here.
"""

import litellm
import pytest
from fastapi.testclient import TestClient

import app.main as api
from schema import PatientLabels

client = TestClient(api.app)

FIXTURE = PatientLabels.model_validate(
    {
        "patient_id": "P000",
        "biologic_prescribed": True,
        "biologic_taken": True,
        "biologic_not_mentioned": False,
        "treatment_outcome": "SUCCESS",
    }
)
BODY = {
    "patient_id": "P000",
    "interview_transcript": "Diagnosed with Crohn's; on Humira.",
}


def test_health_reports_version_and_model():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": api.APP_VERSION, "model": api.MODEL}


def test_schema_returns_patientlabels_schema():
    r = client.get("/schema")
    assert r.status_code == 200 and r.json()["title"] == "PatientLabels"


def test_extract_returns_prediction_stateless_by_default(monkeypatch):
    """200 with the validated record; without ?persist=true the extract call gets out_dir=None."""
    seen = {}

    def fake(transcript, patient_id, out_dir=None):
        seen.update(transcript=transcript, patient_id=patient_id, out_dir=out_dir)
        return FIXTURE

    monkeypatch.setattr(api, "extract", fake)
    r = client.post("/extract", json=BODY)
    assert r.status_code == 200
    assert PatientLabels.model_validate(r.json()) == FIXTURE
    assert seen["patient_id"] == "P000" and seen["out_dir"] is None  # stateless


def test_extract_persist_flag_routes_to_json_dir(monkeypatch):
    """?persist=true opts in to the batch-run behaviour: out_dir = config.JSON_DIR."""
    seen = {}
    monkeypatch.setattr(
        api,
        "extract",
        lambda t, p, out_dir=None: seen.update(out_dir=out_dir) or FIXTURE,
    )
    assert client.post("/extract?persist=true", json=BODY).status_code == 200
    assert seen["out_dir"] == api.JSON_DIR


def test_extract_rejects_bad_body_422():
    """A body missing interview_transcript fails Pydantic validation before any LLM call."""
    assert client.post("/extract", json={"patient_id": "P000"}).status_code == 422


@pytest.mark.parametrize(
    ("error", "status", "hint"),
    [
        (
            litellm.AuthenticationError("auth", "gemini", "gemini/x"),
            500,
            "GEMINI_API_KEY",
        ),
        (litellm.RateLimitError("rate", "gemini", "gemini/x"), 429, "STOP"),
        (litellm.ServiceUnavailableError("busy", "gemini", "gemini/x"), 503, "re-run"),
        (litellm.APIConnectionError("down", "gemini", "gemini/x"), 502, "connection"),
        (
            litellm.JSONSchemaValidationError("gemini/x", "gemini", "{bad", "{}"),
            502,
            "schema",
        ),
    ],
)
def test_extract_maps_handled_errors_to_http_status(monkeypatch, error, status, hint):
    """Each HANDLED upstream error maps to its HTTP status with the give_up_reason action."""

    def boom(*args, **kwargs):
        raise error

    monkeypatch.setattr(api, "extract", boom)
    r = client.post("/extract", json=BODY)
    assert r.status_code == status and hint in r.json()["detail"]
