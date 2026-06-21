"""Unit tests for referral_pathway_analysis on the persisted predictions (offline)."""

import pytest

from referral_pathway_analysis import load_pathways, render
from schema import PathwayStep

CANONICAL = {s.value for s in PathwayStep}


def test_load_pathways_returns_canonical_tokens():
    """load_pathways() yields ordered, canonical PathwayStep tokens per patient."""
    pathways = load_pathways()
    if not pathways:
        pytest.skip("no predictions in data/out yet")
    for pid, seq in pathways.items():
        assert pid.startswith("P") and isinstance(seq, list)
        assert all(step in CANONICAL for step in seq), f"{pid}: non-canonical {seq}"


def test_render_cyclic_uses_force_layout(tmp_path):
    """A pathway that loops (a phase recurs) renders with a force layout + one title + (x2) tooltip."""
    cyclic = [
        "biologic_taken",
        "loss_of_response",
        "biologic_switch",
        "loss_of_response",
        "biologic_switch",
    ]
    html = render("P999", cyclic, tmp_path / "c.html").read_text()
    assert html.count("<h1>Referral pathway: P999</h1>") == 1
    assert (
        "forceAtlas2Based" in html
    )  # cyclic journey -> force layout (loops render as loops)
    assert (
        "(x2)" in html
    )  # loss_of_response -> biologic_switch traversed twice = a loop


def test_render_linear_uses_lr_layout(tmp_path):
    """A linear pathway (no repeats) renders left-to-right for readability."""
    linear = [
        "symptom_onset",
        "specialist_referral",
        "biologic_recommended",
        "biologic_taken",
    ]
    html = render("P998", linear, tmp_path / "l.html").read_text()
    assert '"direction": "LR"' in html
