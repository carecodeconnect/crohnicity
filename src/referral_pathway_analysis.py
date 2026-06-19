"""Explore the 10 candidate referral pathways: phase + transition frequencies, and an
interactive directed graph that keeps the cycles a Sankey can't represent.

Prototype — the PATHWAYS dict is hardcoded for now; later this reads the referral_pathway
column from the ground-truth spreadsheet. Run: uv run python src/referral_pathway_analysis.py
"""

import re
from collections import Counter
from pathlib import Path

import pandas as pd
from pyvis.network import Network

OUT = Path(__file__).resolve().parents[1] / "data" / "out"

# Candidate canonical-event chains for P001-P010 (drafted from the transcripts).
PATHWAYS = {
    "P001": "symptom_onset -> gp_visit -> misdiagnosis(IBS) -> symptoms_worsen -> specialist_referral -> colonoscopy -> crohns_diagnosis -> medication(mesalamine) -> treatment_failed -> medication(azathioprine) -> adverse_reaction -> biologic_recommended(humira) -> patient_fear -> insurance_denial -> insurance_appeal -> insurance_approval -> biologic_taken(humira) -> partial_remission",
    "P002": "symptom_onset -> endocrinologist_visit -> misdiagnosis(gastroparesis) -> symptoms_worsen -> specialist_referral -> diagnostics -> crohns_diagnosis -> steroid(prednisone) -> medication_failed(mesalamine) -> adverse_reaction(methotrexate) -> biologic_recommended(stelara) -> insurance_cost_barrier -> biologic_not_taken -> bridge_therapy(budesonide) -> awaiting_financial_assistance -> journey_unresolved",
    "P003": "symptom_onset -> multiple_gp_visits -> diagnostic_delay -> crohns_diagnosis -> complication(fistula) -> surgery -> medication(sulfasalazine,mesalamine,6mp,methotrexate) -> treatment_failed -> biologic_taken(remicade) -> loss_of_response(antibodies) -> biologic_switch(humira) -> loss_of_response -> biologic_switch(stelara) -> ongoing",
    "P004": "symptom_onset -> self_managed(stress) -> acute_crisis(ER) -> ct_scan -> specialist_referral -> colonoscopy -> crohns_diagnosis -> steroid(prednisone) -> medication_failed(mesalamine) -> adverse_reaction(sulfasalazine) -> biologic_recommended(entyvio) -> insurance_cost_barrier -> biologic_not_taken -> bridge_therapy(budesonide) -> exploring_clinical_trial -> journey_unresolved",
    "P005": "symptom_onset -> misdiagnosis(period/stress) -> specialist_referral -> colonoscopy -> crohns_diagnosis -> medication(mesalamine)+steroid(prednisone) -> relapse -> adverse_reaction(azathioprine->pancreatitis) -> biologic_taken(remicade) -> biologic_switch(humira) -> patient_fear(injections) -> partial_remission",
    "P006": "symptom_onset -> misdiagnosis(ulcerative_colitis) -> diagnostic_delay -> crohns_diagnosis -> complication(strictures) -> surgery(resection) -> adverse_reaction(methotrexate) -> biologic_taken(humira) -> loss_of_response -> insurance_step_therapy -> biologic_switch(remicade) -> loss_of_response(antibodies) -> biologic_switch(stelara) -> ongoing",
    "P007": "symptom_onset -> misdiagnosis(fibromyalgia/thyroid) -> diagnostic_delay -> specialist_referral -> diagnostics -> crohns_diagnosis -> steroid(prednisone)+medication(azathioprine) -> partial_response -> biologic_recommended -> biologic_taken(entyvio) -> partial_remission -> breakthrough_symptoms -> considering_combo_therapy",
    "P008": "symptom_onset -> misdiagnosis(stress) -> acute_crisis(ER) -> colonoscopy -> crohns_diagnosis -> steroid(prednisone)+medication(mesalamine) -> complication(obstruction/surgery) -> medication(methotrexate) -> insurance_step_therapy -> adverse_reaction(6mp->pancreatitis) -> biologic_taken(remicade) -> loss_of_response -> biologic_switch(humira) -> waning_response -> considering_switch",
    "P009": "symptom_onset -> misdiagnosis(IBS/anxiety) -> diagnostic_delay -> acute_crisis(hospitalization) -> colonoscopy -> crohns_diagnosis -> medication(mesalamine) -> steroid(prednisone) -> adverse_reaction(azathioprine) -> biologic_recommended -> patient_fear(needle_phobia) -> alternative_therapy(diet/acupuncture) -> acute_crisis -> biologic_taken(entyvio) -> loss_of_response -> comorbidity(RA) -> add_medication(methotrexate) -> considering_switch(stelara)",
    "P010": "symptom_onset -> gp_visit -> abnormal_labs(CRP) -> specialist_referral -> colonoscopy -> crohns_diagnosis -> triple_therapy(prednisone,azathioprine,mesalamine) -> remission -> comorbidity(arthritis) -> medication_switch(methotrexate) -> crohns_flare -> biologic_recommended -> insurance_denial -> insurance_appeal -> insurance_approval -> biologic_taken(humira) -> partial_remission -> considering_switch(stelara)",
}


# Consolidated canonical phase vocabulary (raw phases -> tighter set).
# PENDING domain-expert sign-off. NOTE: loss_of_response here means *secondary* loss of
# response (the drug worked, then stopped — e.g. anti-drug antibodies), NOT primary
# non-response (drug never worked); the latter maps to therapy_failed.
PHASE_MAP = {
    "gp_visit": "primary_care_contact",
    "multiple_gp_visits": "primary_care_contact",
    "endocrinologist_visit": "primary_care_contact",
    "colonoscopy": "diagnostic_testing",
    "diagnostics": "diagnostic_testing",
    "ct_scan": "diagnostic_testing",
    "abnormal_labs": "diagnostic_testing",
    "medication": "conventional_therapy",
    "steroid": "conventional_therapy",
    "triple_therapy": "conventional_therapy",
    "bridge_therapy": "conventional_therapy",
    "add_medication": "conventional_therapy",
    "medication_switch": "conventional_therapy",
    "steroid+medication": "conventional_therapy",  # fixes the +-order duplicate
    "medication+steroid": "conventional_therapy",
    "medication_failed": "therapy_failed",
    "treatment_failed": "therapy_failed",
    "waning_response": "loss_of_response",
    "acute_crisis": "acute_flare",
    "crohns_flare": "acute_flare",
    "partial_remission": "remission",
    "partial_response": "remission",
    "considering_switch": "planning_next_step",
    "considering_combo_therapy": "planning_next_step",
    "ongoing": "unresolved",
    "journey_unresolved": "unresolved",
    "awaiting_financial_assistance": "unresolved",
    "exploring_clinical_trial": "unresolved",
}


def phases(chain: str) -> list[str]:
    """Canonical phase tokens: drop (detail) annotations, split on '->', then consolidate."""
    raw = (p.strip() for p in re.sub(r"\([^)]*\)", "", chain).split("->") if p.strip())
    return [PHASE_MAP.get(p, p) for p in raw]


def render(pathways: dict[str, str], path: Path, heading: str) -> Path:
    """Write an interactive directed graph (cycles allowed) for the given pathways."""
    nodes, edges = Counter(), Counter()
    for seq in map(phases, pathways.values()):
        nodes.update(seq)
        edges.update(zip(seq, seq[1:]))
    net = Network(
        directed=True,
        height="750px",
        width="100%",
        cdn_resources="in_line",
        heading=heading,
    )
    for phase, count in nodes.items():
        net.add_node(phase, label=phase, value=count)
    for (s, d), count in edges.items():
        net.add_edge(s, d, value=count, title=f"{s} -> {d}: {count}")
    net.write_html(str(path), notebook=False, open_browser=False)
    return path


def main() -> None:
    """Print phase/transition frequency tables and write per-case journey graphs."""
    nodes, edges = Counter(), Counter()
    for seq in map(phases, PATHWAYS.values()):
        nodes.update(seq)
        edges.update(zip(seq, seq[1:]))

    phase_freq = pd.DataFrame(nodes.most_common(), columns=["phase", "count"])
    transitions = pd.DataFrame(
        [(a, b, c) for (a, b), c in edges.most_common()],
        columns=["from_phase", "to_phase", "count"],
    )
    print(
        f"{len(PATHWAYS)} pathways - {len(nodes)} distinct phases - {sum(edges.values())} transitions\n"
    )
    print("PHASE FREQUENCY\n", phase_freq.to_string(index=False), "\n")
    print("TRANSITIONS (most common first)\n", transitions.to_string(index=False))

    OUT.mkdir(parents=True, exist_ok=True)
    # A journey graph is meaningful PER CASE only: overlaying patients merges distinct
    # journeys into spurious shared nodes. Start with singular examples across the complexity
    # range (P005 simplest, P003 a cyclic antibody-driven switcher); journey-TYPE clustering later.
    for pid in ("P005", "P003"):
        out = render(
            {pid: PATHWAYS[pid]},
            OUT / f"referral_pathway_{pid}.html",
            f"Referral pathway: {pid}",
        )
        print(f"{pid} graph -> {out}")


if __name__ == "__main__":
    main()
