"""Unit test: the validation/holdout split derives purely from the to_review flag."""

import pandas as pd

from splits import split_ids


def test_split_ids_from_to_review():
    """to_review truthy -> validation; blank/false -> holdout; the two never overlap."""
    df = pd.DataFrame(
        {
            "patient_id": ["P001", "P002", "P003", "P004"],
            "to_review": ["TRUE", "FALSE", "TRUE", None],
        }
    )
    validation, holdout = split_ids(df)

    assert validation == ["P001", "P003"]
    assert holdout == ["P002", "P004"]
    assert set(validation).isdisjoint(holdout)
