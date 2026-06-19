"""Pydantic schema for one patient's ground-truth labels.

Mirrors the columns and controlled vocabularies in `docs/SCHEMA.md` (v0.3) and the data in
`data/in/interviews_ground_truth_v3.ods`. Field names match the spreadsheet column names so
annotations map 1:1, and this is the contract the LiteLLM/Gemini extraction must return.

Two spreadsheet columns are intentionally *not* modelled here: `interview_transcript` (it's the
model's *input*, not an extracted label) and `to_review` (a human-set validation/holdout flag —
see `src/splits.py` — not something the model produces).

The rationale for each name/type is in `docs/SCHEMA.md`; the docstrings below summarise it.
"""

from enum import Enum

from pydantic import BaseModel


class TreatmentOutcome(str, Enum):
    """Overall outcome. `AMBIGUOUS`/`ONGOING` exist because Crohn's journeys are often circular —
    forcing every patient into SUCCESS/FAILED would fabricate a certainty the transcripts lack."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"  # stated but mixed / contradictory
    ONGOING = "ONGOING"  # unresolved / still escalating
    UNKNOWN = "UNKNOWN"  # not stated


class ReasonPrescribed(str, Enum):
    """Why a biologic *was* the chosen path."""

    DOCTOR_CHOICE = "DOCTOR_CHOICE"
    PATIENT_FEARS = "PATIENT_FEARS"
    COST = "COST"
    ACCESS = "ACCESS"
    NOT_APPLICABLE = "NOT_APPLICABLE"  # no biologic prescribed -> field doesn't apply
    OTHER = "OTHER"


class ReasonNotTaken(str, Enum):
    """Why a prescribed biologic wasn't taken / wasn't reached.

    `PATIENT_FEARS` lives here (fear of needles/side-effects blocks *taking*, not prescribing);
    `CONTRAINDICATION` and `DEFERRED` were added from real cases (e.g. COPD risk; post-surgery).
    `NOT_APPLICABLE` distinguishes "doesn't apply" (biologic was taken) from a blank "not yet
    annotated" cell.
    """

    NOT_MENTIONED = "NOT_MENTIONED"
    EXPLICIT_DENIAL = "EXPLICIT_DENIAL"
    INSURANCE_PROBLEMS = "INSURANCE_PROBLEMS"  # denial / auth / tier / step-therapy
    COST = "COST"  # affordability even when covered
    PATIENT_FEARS = "PATIENT_FEARS"  # fear of needles / side-effects
    CONTRAINDICATION = "CONTRAINDICATION"  # medically can't be given (e.g. COPD)
    DEFERRED = "DEFERRED"  # appropriate but postponed (e.g. awaiting surgery recovery)
    JOURNEY_CUT_OFF = "JOURNEY_CUT_OFF"  # transcript ends before the journey resolves
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"  # biologic was taken -> field doesn't apply
    OTHER = "OTHER"


class ComorbidCondition(str, Enum):
    """Independent coexisting diagnoses only — NOT Crohn's-driven sequelae (psoriasis,
    osteoporosis, etc.). Lumping treatment/disease effects in here would make a later "does
    comorbidity X predict outcome Y" analysis circular. Seeded from P001-P050; extend as found.
    """

    TYPE_2_DIABETES = "TYPE_2_DIABETES"
    HYPERTENSION = "HYPERTENSION"
    HYPERLIPIDEMIA = "HYPERLIPIDEMIA"
    ANXIETY_DISORDER = "ANXIETY_DISORDER"
    DEPRESSION = "DEPRESSION"
    PCOS = "PCOS"
    ENDOMETRIOSIS = "ENDOMETRIOSIS"
    MIGRAINE = "MIGRAINE"
    HYPOTHYROIDISM = "HYPOTHYROIDISM"
    FIBROMYALGIA = "FIBROMYALGIA"
    ASTHMA = "ASTHMA"
    RHEUMATOID_ARTHRITIS = "RHEUMATOID_ARTHRITIS"
    ADHD = "ADHD"
    SLEEP_APNEA = "SLEEP_APNEA"
    OTHER = "OTHER"


class PathwayStep(str, Enum):
    """Canonical referral-pathway steps — the draft vocabulary already used to render the
    per-case journey graphs in `data/out/*.html` (mirrors the consolidated phases in
    `src/referral_pathway_analysis.py`). Values are lowercase to match those graph tokens.

    Minimal for this iteration: enough to type `referral_pathway` and drive the diagrams. A
    dedicated extraction prompt fills this field; the eventual goal is clustering these per-case
    chains into journey *types* (`docs/SCHEMA.md`). `OTHER` absorbs steps not yet in the vocab.
    """

    # diagnostic journey
    SYMPTOM_ONSET = "symptom_onset"
    SELF_MANAGED = "self_managed"
    PRIMARY_CARE_CONTACT = "primary_care_contact"
    MISDIAGNOSIS = "misdiagnosis"
    DIAGNOSTIC_DELAY = "diagnostic_delay"
    SYMPTOMS_WORSEN = "symptoms_worsen"
    SPECIALIST_REFERRAL = "specialist_referral"
    DIAGNOSTIC_TESTING = "diagnostic_testing"
    CROHNS_DIAGNOSIS = "crohns_diagnosis"
    # conventional therapy
    CONVENTIONAL_THERAPY = "conventional_therapy"
    THERAPY_FAILED = "therapy_failed"
    ADVERSE_REACTION = "adverse_reaction"
    RELAPSE = "relapse"
    # acute events / complications / comorbidity
    ACUTE_FLARE = "acute_flare"
    COMPLICATION = "complication"
    SURGERY = "surgery"
    COMORBIDITY = "comorbidity"
    # biologic funnel
    BIOLOGIC_RECOMMENDED = "biologic_recommended"
    PATIENT_FEAR = "patient_fear"
    INSURANCE_DENIAL = "insurance_denial"
    INSURANCE_APPEAL = "insurance_appeal"
    INSURANCE_APPROVAL = "insurance_approval"
    INSURANCE_COST_BARRIER = "insurance_cost_barrier"
    INSURANCE_STEP_THERAPY = "insurance_step_therapy"
    BIOLOGIC_NOT_TAKEN = "biologic_not_taken"
    BIOLOGIC_TAKEN = "biologic_taken"
    BIOLOGIC_SWITCH = "biologic_switch"
    LOSS_OF_RESPONSE = "loss_of_response"
    # outcome / status
    REMISSION = "remission"
    BREAKTHROUGH_SYMPTOMS = "breakthrough_symptoms"
    ALTERNATIVE_THERAPY = "alternative_therapy"
    PLANNING_NEXT_STEP = "planning_next_step"
    UNRESOLVED = "unresolved"
    OTHER = "other"


class Demographics(BaseModel):
    """Self-reported gender/age, grouped so we can later test for demographic differences in
    pathways/outcomes. The flat `gender`/`age` spreadsheet columns map into this sub-model."""

    gender: str | None = None
    age: int | None = None


class TreatmentRecord(BaseModel):
    """One treatment in the patient's history. The free-text `treatment_records` column parses
    into a list of these later; kept minimal until the annotation convention firms up."""

    name: str
    treatment_class: str
    outcome: TreatmentOutcome
    reason_stopped: str | None = None


class PatientGroundTruth(BaseModel):
    """One patient's gold-standard labels — the contract the extraction pipeline must return.

    Field names match the v3 spreadsheet columns 1:1 (see `docs/SCHEMA.md`). Required fields are
    the ones every transcript can answer; the rest default to `None`/`[]` so a partial extraction
    still validates.
    """

    patient_id: str

    # Optional because their definitions are unresolved (CAIO) and may not be derivable from
    # transcripts at all — see the open questions in docs/SCHEMA.md and docs/QUESTIONS.md.
    churn: bool | None = None
    incomplete_journey: bool | None = None

    demographics: Demographics = Demographics()

    biologic_prescribed: bool
    # prescribed != taken — the key distinction in the biologic funnel
    biologic_taken: bool
    # separates "topic absent" from "explicitly not prescribed"
    biologic_not_mentioned: bool
    biologic_type: str | None = None

    reasons_for_biologic_prescribed: ReasonPrescribed | None = None
    reasons_for_biologic_not_taken: ReasonNotTaken | None = None

    comorbid_conditions: list[ComorbidCondition] = []
    treatment_records: list[TreatmentRecord] = []
    treatment_outcome: TreatmentOutcome

    # Minimal typed pathway this iteration: an ordered list of canonical PathwayStep tokens (the
    # draft step names already used to render data/out/*.html). Filled by a dedicated prompt;
    # clustering into journey TYPES comes later (docs/SCHEMA.md).
    referral_pathway: list[PathwayStep] = []

    evidence_notes: str | None = None  # deferred — citing per-field sources is costly
