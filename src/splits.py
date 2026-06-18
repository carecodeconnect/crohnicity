"""Validation / holdout split, derived from the `to_review` flag in the ground-truth
spreadsheet — the single source of truth.

`to_review` truthy  -> validation (annotated, used to develop the LiteLLM/Gemini prompts).
`to_review` falsy/blank -> holdout (never seen during prompt development).

Deliberately holds NO hardcoded case IDs: deriving the split from the flag is what stops the
two from drifting out of sync.
"""

from pathlib import Path

import pandas as pd

_TRUE = {"true", "1", "1.0", "yes"}


def is_review(series: pd.Series) -> pd.Series:
    """Boolean mask of `to_review`, tolerant of TRUE/FALSE text, bools, or 1/0."""
    return series.map(lambda v: str(v).strip().lower() in _TRUE)


def split_ids(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Return (validation_ids, holdout_ids) from the `to_review` column."""
    review = is_review(df["to_review"])
    return df.loc[review, "patient_id"].tolist(), df.loc[~review, "patient_id"].tolist()


def load_splits(ods_path: str | Path) -> tuple[list[str], list[str]]:
    """Read the ground-truth `.ods` and split by `to_review`."""
    return split_ids(pd.read_excel(ods_path, engine="odf"))
