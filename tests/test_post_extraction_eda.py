"""Unit tests for src/post_extraction_eda.py — the post-extraction EDA functions.

Deterministic: they read the persisted predictions in data/out/ and the gold _v5.ods (no API call),
so the same artefacts the README.qmd renders from are the ones under test.
"""

import math

import post_extraction_eda as eda

RECORDS = eda.load_records()
DF = eda.load_predictions()


def test_load_predictions_one_row_per_patient() -> None:
    assert len(RECORDS) == len(DF) == 50
    assert {"patient_id", "biologic_taken", "churn"} <= set(DF.columns)


def test_q1_share_sums_to_cohort() -> None:
    q1 = eda.q1_share(DF)
    assert int(q1["patients"].sum()) == len(DF)
    assert int(q1.loc[0, "patients"]) == int(DF["biologic_taken"].sum())


def test_gold_eval_matches_documented_metrics() -> None:
    """The 19-case to_review gold split documented in the README (TP/FP/FN/TN = 9/1/0/9)."""
    ev = eda.gold_eval(DF)
    assert ev["n"] == 19
    assert (ev["tp"], ev["fp"], ev["fn"], ev["tn"]) == (9, 1, 0, 9)
    assert math.isclose(ev["precision"], 0.9)
    assert ev["recall"] == 1.0


def test_q2_reasons_counts_patients_not_on_biologic() -> None:
    q2 = eda.q2_reasons(DF)
    assert list(q2.columns) == ["reason", "patients"]
    assert int(q2["patients"].sum()) == int((~DF["biologic_taken"]).sum())


def test_q3_before_biologic_nonempty() -> None:
    q3 = eda.q3_before_biologic(RECORDS)
    assert list(q3.columns) == ["treatment_class", "mentions"]
    assert int(q3["mentions"].sum()) > 0


def test_steps_to_biologic_counts_from_start() -> None:
    assert eda.steps_to_biologic(["a", "biologic_recommended"]) == 1
    assert (
        eda.steps_to_biologic(["primary_care_contact", "x", "biologic_recommended"])
        == 2
    )
    assert eda.steps_to_biologic(["symptom_onset"]) is None


def test_q4_distribution_matches_recommended_count() -> None:
    q4 = eda.q4_step_distribution(RECORDS)
    assert list(q4.columns) == ["steps", "patients"]
    assert int(q4["patients"].sum()) == eda.count_pathway_step(
        RECORDS, "biologic_recommended"
    )


def test_churn_three_state_three_rows() -> None:
    ts = eda.churn_three_state(DF)
    assert list(ts["state"]) == [
        "biologic not mentioned (absence)",
        "discussed but not taken (negation)",
        "churned / truncated",
    ]
    assert bool((ts["patients"] >= 0).all())
