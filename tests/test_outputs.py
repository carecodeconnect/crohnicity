"""Validate the persisted prediction outputs in data/out/ (one JSON per patient).

These are real model outputs written by extract.py. This guards that every committed prediction
still conforms to the current `PatientLabels` schema — which, since `referral_pathway`, the reason
fields and `treatment_outcome` are typed enums, also enforces that those values stay canonical —
and that each `patient_id` matches its filename. Offline (no API call); skips if none exist yet.
"""

from pathlib import Path

import pytest

from schema import PatientLabels

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "out"
PREDICTIONS = sorted(
    OUT_DIR.glob("P[0-9][0-9][0-9].json")
)  # per-patient predictions only


def test_persisted_predictions_valid() -> None:
    """Every data/out/P###.json re-validates as PatientLabels with id matching its filename."""
    if not PREDICTIONS:
        pytest.skip("no prediction JSONs in data/out yet")
    for path in PREDICTIONS:
        labels = PatientLabels.model_validate_json(path.read_text())
        assert labels.patient_id == path.stem, f"{path.name}: id={labels.patient_id}"
