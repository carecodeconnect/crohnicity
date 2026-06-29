"""Unit tests for src/post_extraction_eda.py — the post-extraction EDA functions.

Deterministic: they read the persisted predictions in data/out/ and the gold .ods (config.GOLD; no API call),
so the same artefacts the README.qmd renders from are the ones under test.
"""

import math

import pandas as pd

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
    """The 20-case to_review gold set documented in the README (TP/FP/FN/TN = 9/1/0/10)."""
    ev = eda.gold_eval(DF)
    assert ev["n"] == 20
    assert (ev["tp"], ev["fp"], ev["fn"], ev["tn"]) == (9, 1, 0, 10)
    assert math.isclose(ev["precision"], 0.9)
    assert ev["recall"] == 1.0


def test_q2_reasons_counts_patients_not_on_biologic() -> None:
    q2 = eda.q2_reasons(DF)
    assert list(q2.columns) == ["reason", "mentions"]
    # reasons are multi-select now, so mentions >= one per not-on-biologic patient
    assert int(q2["mentions"].sum()) >= int((~DF["biologic_taken"]).sum())


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


def test_churn_false_negatives_flags_gold_churn_the_model_missed() -> None:
    """churn_false_negatives() reports the gold churn==1 cases the model failed to flag. Tested on
    the function's *logic* against the real gold anchor (P049 is gold churn==1 & to_review==1), not
    a specific run — the live result is dynamic (the -flash run now catches P049, so it is currently
    empty). Powers the README churn note, so the function must not regress silently."""
    # model MISSED P049's churn -> it must be reported as a false negative
    missed = pd.DataFrame({"patient_id": ["P049"], "churn": [False]}, dtype=object)
    assert eda.churn_false_negatives(missed) == ["P049"]
    # model CAUGHT P049's churn -> it must NOT be reported
    caught = pd.DataFrame({"patient_id": ["P049"], "churn": [True]}, dtype=object)
    assert eda.churn_false_negatives(caught) == []


def test_pathway_mermaid_renders_a_cyclic_example() -> None:
    """`pick_cyclic_example` returns a looping journey and `pathway_mermaid` emits a
    GitHub-renderable mermaid block for it (one node per distinct phase). Powers the Q4 teaser."""
    pid = eda.pick_cyclic_example(RECORDS)
    seq = next(r["referral_pathway"] for r in RECORDS if r["patient_id"] == pid)
    assert len(seq) != len(set(seq))  # genuinely cyclic — a phase recurs
    block = eda.pathway_mermaid(RECORDS, pid)
    assert block.startswith("```mermaid")
    assert block.rstrip().endswith("```")
    assert "flowchart LR" in block
    assert all(f'n{i}["' in block for i in range(len(set(seq))))
