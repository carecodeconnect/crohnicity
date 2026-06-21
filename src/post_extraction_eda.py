"""Post-extraction EDA — pure functions over the persisted predictions in ``data/out/``.

This is the phase *after* the inference loop: it reads only the validated prediction JSON
(and the gold ``.ods`` for the eval), never the Gemini API. Both the ``README.qmd`` chunks and
the (future) Dagster EDA asset import these, so the **computation lives here** (reusable, testable)
and the ``.qmd`` keeps only presentation (plots, tables, prose). See ``docs/TODO.md``.
"""

import json
from pathlib import Path

import pandas as pd

from config import GOLD, JSON_DIR


def load_records(out_dir: Path = JSON_DIR) -> list[dict]:
    """Raw prediction dicts (nested ``treatment_records`` / ``referral_pathway`` intact), by id."""
    return [
        json.loads(p.read_text()) for p in sorted(out_dir.glob("P[0-9][0-9][0-9].json"))
    ]


def load_predictions(out_dir: Path = JSON_DIR) -> pd.DataFrame:
    """Flat one-row-per-patient frame (nested fields json-normalised)."""
    return pd.json_normalize(load_records(out_dir))


def count_pathway_step(records: list[dict], step: str) -> int:
    """How many patients' ``referral_pathway`` contains ``step`` (e.g. ``primary_care_contact``)."""
    return sum(step in r["referral_pathway"] for r in records)


def q1_share(df: pd.DataFrame) -> pd.DataFrame:
    """Q1 — patients on vs. not on a biologic (``biologic_taken``), with percentages."""
    on = int(df["biologic_taken"].sum())
    n = len(df)
    return pd.DataFrame(
        {
            "status": ["on a biologic (taken)", "not on a biologic"],
            "patients": [on, n - on],
            "pct": [round(100 * on / n, 1), round(100 * (n - on) / n, 1)],
        }
    )


def gold_eval(
    df: pd.DataFrame, gold_path: Path = GOLD, field: str = "biologic_taken"
) -> dict[str, float]:
    """Precision / recall / F1 / accuracy of ``field`` against the gold ``to_review`` split."""
    gold = pd.read_excel(gold_path, engine="odf")
    gold = gold.loc[gold["to_review"] == 1, ["patient_id", field]].dropna()
    ev = gold.merge(
        df[["patient_id", field]], on="patient_id", suffixes=("_gold", "_pred")
    )
    g = ev[f"{field}_gold"].astype(bool)
    p = ev[f"{field}_pred"].astype(bool)
    tp = int((p & g).sum())
    fp = int((p & ~g).sum())
    fn = int((~p & g).sum())
    tn = int((~p & ~g).sum())
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "accuracy": (tp + tn) / len(ev) if len(ev) else float("nan"),
        "n": len(ev),
    }


def q2_reasons(df: pd.DataFrame) -> pd.DataFrame:
    """Q2 — reasons not on a biologic, counted over patients not on one."""
    not_on = df[~df["biologic_taken"]]
    return (
        not_on["reasons_for_biologic_not_taken"]
        .fillna("unspecified")
        .value_counts()
        .rename_axis("reason")
        .reset_index(name="patients")
    )


def q3_before_biologic(records: list[dict]) -> pd.DataFrame:
    """Q3 — treatment classes tried before a biologic (``before_biologic == true``)."""
    before = [
        (t.get("treatment_class") or t.get("name"))
        for r in records
        for t in r["treatment_records"]
        if t.get("before_biologic")
    ]
    return (
        pd.Series(before)
        .value_counts()
        .rename_axis("treatment_class")
        .reset_index(name="mentions")
    )


def steps_to_biologic(pathway: list[str]) -> int | None:
    """Steps from journey start (or ``primary_care_contact``) to ``biologic_recommended``."""
    if "biologic_recommended" not in pathway:
        return None
    start = (
        pathway.index("primary_care_contact")
        if "primary_care_contact" in pathway
        else 0
    )
    return pathway.index("biologic_recommended") - start


def q4_steps(records: list[dict]) -> pd.Series:
    """Per-patient step counts to ``biologic_recommended`` (patients without it dropped)."""
    return pd.Series(
        [steps_to_biologic(r["referral_pathway"]) for r in records], dtype="Float64"
    ).dropna()


def q4_step_distribution(records: list[dict]) -> pd.DataFrame:
    """Q4 — distribution of step counts (``steps`` / ``patients``), sorted by frequency."""
    return (
        q4_steps(records)
        .astype(int)
        .value_counts()
        .rename_axis("steps")
        .reset_index(name="patients")
    )


def n_cyclic(records: list[dict]) -> int:
    """How many journeys loop — a phase recurs (``len(pathway) != len(set(pathway))``)."""
    return sum(
        len(r["referral_pathway"]) != len(set(r["referral_pathway"])) for r in records
    )


def churn_three_state(df: pd.DataFrame) -> pd.DataFrame:
    """The absence / negation / truncation three-way split the analysis needs."""
    return pd.DataFrame(
        {
            "state": [
                "biologic not mentioned (absence)",
                "discussed but not taken (negation)",
                "churned / truncated",
            ],
            "patients": [
                int(df["biologic_not_mentioned"].sum()),
                int((df["biologic_prescribed"] & ~df["biologic_taken"]).sum()),
                int(df["churn"].eq(True).sum()),
            ],
        }
    )


def churn_false_negatives(df: pd.DataFrame, gold_path: Path = GOLD) -> list[str]:
    """Patient IDs the gold marks as churn but the model missed (gold churn==1, model not True) —
    the false negatives behind the low churn count. Computed at render time so prose stays dynamic."""
    gold = pd.read_excel(gold_path, engine="odf")
    flagged = gold.loc[(gold["to_review"] == 1) & (gold["churn"] == 1), "patient_id"]
    model_churn = dict(zip(df["patient_id"], df["churn"]))
    return [pid for pid in flagged if model_churn.get(pid) is not True]
