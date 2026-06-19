"""Unit test for the referral_pathway phase parser, on a single dataset sample (P005)."""

from referral_pathway_analysis import PATHWAYS, phases


def test_phases_on_p005_sample():
    """phases() drops (detail) annotations, splits on '->', and applies consolidation."""
    result = phases(PATHWAYS["P005"])

    assert (
        result
        == [
            "symptom_onset",
            "misdiagnosis",
            "specialist_referral",
            "diagnostic_testing",  # colonoscopy -> consolidated
            "crohns_diagnosis",
            "conventional_therapy",  # medication(...)+steroid(...) -> consolidated, +-order fixed
            "relapse",
            "adverse_reaction",  # (azathioprine->pancreatitis) detail dropped, inner '->' ignored
            "biologic_taken",
            "biologic_switch",
            "patient_fear",
            "remission",  # partial_remission -> consolidated
        ]
    )
    # no (detail) annotation leaks through to a canonical phase
    assert all("(" not in phase for phase in result)
