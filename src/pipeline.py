"""Dagster view of the pipeline — see which step fails (and why) in a UI.

    uv run dagster dev -f src/pipeline.py        # then open http://127.0.0.1:3000

Two assets: `interviews` (load + validate) -> `predictions` (one extract() per patient). A failure
(rate limit, schema mismatch, connection) shows on the failing asset with the logged error, so the
source is visible at a glance. The model comes from `config` — the CROHNICITY_MODEL env var
overrides the config.json default.
"""

import dagster as dg

from config import MODEL
from extract import extract
from main import load_interviews
from schema import Interview, PatientLabels


@dg.asset
def interviews() -> list[Interview]:
    """Load + validate data/in/interviews.json."""
    return load_interviews()


@dg.asset
def predictions(interviews: list[Interview]) -> list[PatientLabels]:
    """One extract() per interview; a failure surfaces on this asset in the UI."""
    return [
        extract(r.interview_transcript, r.patient_id, model=MODEL) for r in interviews
    ]


defs = dg.Definitions(assets=[interviews, predictions])
