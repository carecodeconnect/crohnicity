# Ground-truth annotation schema (v0.2)

Columns in the ground-truth spreadsheet that stakeholders fill in to create the **gold set**
of labels for evaluating the extraction pipeline.

> **Status: provisional.** This annotation exercise is what produces the Pydantic schema —
> expect change. Controlled vocabularies below are the single source of truth; mirror them as
> spreadsheet dropdowns. Open business questions live in `docs/QUESTIONS.md`; the pathway
> vocabulary needs domain-expert sign-off (`docs/TODO.md`).

- **Working file:** `data/in/interviews_ground_truth_v2.ods` (generated from the annotated
  `interviews_ground_truth.ods` — see "How v2 is generated").
- **Rows:** 50 patients (`P001`–`P050`).
- **Source columns** (`patient_id`, `interview_transcript`) come from `interviews.json` — **do not edit**.
- **Note:** in `.ods`, booleans persist as `1.0`/`0.0` (LibreOffice), blanks as empty.

## Columns (v2 — 18, in sheet order)

| # | Column | Type | Allowed values | Notes |
|---|--------|------|----------------|-------|
| 1 | `patient_id` | `str` | — | Primary key. **Read-only.** |
| 2 | `interview_transcript` | `str` | — | Full interview text. **Read-only.** |
| 3 | `to_review` | `bool` | `TRUE`/`FALSE` | **NEW.** `TRUE` = case is in the annotation scope; filter on this. |
| 4 | `churn` | `bool` | `TRUE`/`FALSE` | Disengagement — **meaning unresolved** (app vs treatment), see `QUESTIONS.md`. |
| 5 | `incomplete_journey` | `bool` | `TRUE`/`FALSE` | Treatment journey unresolved in the transcript. |
| 6 | `gender` | `str` | free text | **NEW.** Self-reported (`female`/`male` as stated) → `Demographics`. |
| 7 | `age` | `int` | — | **NEW.** Self-reported → `Demographics`. |
| 8 | `biologic_prescribed` | `bool` | `TRUE`/`FALSE` | Was a biologic prescribed/recommended at any point? |
| 9 | `biologic_taken` | `bool` | `TRUE`/`FALSE` | Did the patient actually start/take one? (Prescribed ≠ taken.) |
| 10 | `biologic_not_mentioned` | `bool` | `TRUE`/`FALSE` | `TRUE` when biologics never come up at all. |
| 11 | `biologic_type` | `str` | free text | Named biologic(s), e.g. `Humira`, `infliximab`. |
| 12 | `reasons_for_biologic_prescribed` | `enum` | see vocab | Why a biologic *was* the chosen path. |
| 13 | `reasons_for_biologic_not_taken` | `enum` | see vocab | **RENAMED** from `reasons_for_biologic_denied`; enum expanded. Why a prescribed biologic wasn't taken / wasn't reached. |
| 14 | `comorbid_conditions` | `list[enum]` | see vocab | **NEW.** Independent coexisting diagnoses (not Crohn's sequelae). Comma-separated. |
| 15 | `treatment_records` | `list[TreatmentRecord]` (free text) | see convention | All treatments, in order. |
| 16 | `treatment_outcome` | `enum` | see vocab | Overall patient-level outcome; `AMBIGUOUS`/`ONGOING` added for circular journeys. |
| 17 | `referral_pathway` | `list[str]` (free text) | see convention | Canonical-event journey chain. |
| 18 | `evidence_notes` | `str` | free text | **DEFERRED** — kept as a column, not populated yet (citing per-field sources is costly). |

## Controlled vocabularies

- **Booleans** (`to_review`, `churn`, `incomplete_journey`, `biologic_prescribed`, `biologic_taken`, `biologic_not_mentioned`): `TRUE`, `FALSE`
- **`reasons_for_biologic_prescribed`**: `DOCTOR_CHOICE`, `PATIENT_FEARS`, `COST`, `ACCESS`, `NOT_APPLICABLE`, `OTHER`
- **`reasons_for_biologic_not_taken`**: `NOT_MENTIONED`, `EXPLICIT_DENIAL`, `INSURANCE_PROBLEMS`, `COST`, `PATIENT_FEARS`, `CONTRAINDICATION`, `DEFERRED`, `JOURNEY_CUT_OFF`, `UNKNOWN`, `NOT_APPLICABLE`, `OTHER`
  - *`CONTRAINDICATION` = medically can't be given (e.g. COPD risk); `DEFERRED` = appropriate but postponed (awaiting surgery recovery / timing).*
  - *`NOT_APPLICABLE` (in both reasons enums) = the field genuinely doesn't apply (no biologic prescribed, or it was taken) — distinct from a blank cell, which means "not yet annotated".*
  - *(`PATIENT_FEARS` belongs here — fear of needles/side-effects is a reason a biologic isn't taken, not prescribed. `INSURANCE_PROBLEMS` = denial/auth/tier; `COST` = affordability even when covered.)*
- **`treatment_outcome`** (and `TreatmentRecord.outcome`): `SUCCESS`, `FAILED`, `PARTIAL`, `AMBIGUOUS`, `ONGOING`, `UNKNOWN`
  - *(`AMBIGUOUS` = stated but mixed/contradictory; `ONGOING` = unresolved/still escalating; `UNKNOWN` = not stated.)*
- **`comorbid_conditions`** (seeded from P001–P050; extend as found): `TYPE_2_DIABETES`, `HYPERTENSION`, `HYPERLIPIDEMIA`, `ANXIETY_DISORDER`, `DEPRESSION`, `PCOS`, `ENDOMETRIOSIS`, `MIGRAINE`, `HYPOTHYROIDISM`, `FIBROMYALGIA`, `ASTHMA`, `RHEUMATOID_ARTHRITIS`, `ADHD`, `SLEEP_APNEA`, `OTHER`
  - *Excludes Crohn's-driven sequelae (psoriasis, osteoporosis, anemia, short-bowel, enteropathic arthritis) — those are treatment/disease effects, not independent risk factors.*

## `referral_pathway` — canonical phases

Free text per case for now (arrow-delimited), e.g.:
`symptom_onset -> gp_visit -> misdiagnosis(IBS) -> specialist_referral -> colonoscopy -> crohns_diagnosis -> medication(mesalamine) -> adverse_reaction -> biologic_recommended -> insurance_denial -> biologic_taken(humira) -> partial_remission`

The analysis tool `src/referral_pathway_analysis.py` consolidates raw phases into a tighter
canonical set (`PHASE_MAP`) and renders **per-case** journey graphs (a graph is meaningful per
patient, never aggregated). Consolidated phases (pending domain-expert sign-off):
`primary_care_contact`, `diagnostic_testing`, `conventional_therapy`, `therapy_failed`,
`biologic_recommended`, `biologic_taken`, `biologic_not_taken`, `biologic_switch`,
`loss_of_response`, `acute_flare`, `remission`, `planning_next_step`, `unresolved`, plus
`symptom_onset`, `misdiagnosis`, `crohns_diagnosis`, `specialist_referral`, the `insurance_*`
steps, `complication`, `surgery`, `comorbidity`, `patient_fear`.

- **`loss_of_response`** = *secondary* loss of response (worked, then waned — e.g. anti-drug
  antibodies). *Primary* non-response → `therapy_failed`. **Needs clinician sign-off.**
- **Eventual goal:** cluster per-case pathways into canonical **journey types**.

## Free-text conventions (until structured)

- **`referral_pathway`** — arrow-delimited canonical events (see above). `(detail)` annotations
  are dropped by the analysis tool; the inner text is for the human reviewer.
- **`treatment_records`** — one treatment per line, `name | treatment_class | outcome | reason_stopped`:
  ```
  Prednisone | corticosteroid | FAILED | intolerable side effects
  Infliximab | biologic | SUCCESS |
  ```
- **`comorbid_conditions`** — comma-separated canonical tokens, e.g. `TYPE_2_DIABETES, RHEUMATOID_ARTHRITIS`.

## Toward a Pydantic schema

Target model (not implemented yet — recorded so annotation maps cleanly onto code):

```python
from enum import Enum
from pydantic import BaseModel

class TreatmentOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"   # stated but mixed / contradictory
    ONGOING = "ONGOING"       # unresolved / still escalating
    UNKNOWN = "UNKNOWN"       # not stated

class ReasonPrescribed(str, Enum):
    DOCTOR_CHOICE = "DOCTOR_CHOICE"
    PATIENT_FEARS = "PATIENT_FEARS"
    COST = "COST"
    ACCESS = "ACCESS"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    OTHER = "OTHER"

class ReasonNotTaken(str, Enum):     # renamed from ReasonDenied; expanded
    NOT_MENTIONED = "NOT_MENTIONED"
    EXPLICIT_DENIAL = "EXPLICIT_DENIAL"
    INSURANCE_PROBLEMS = "INSURANCE_PROBLEMS"
    COST = "COST"
    PATIENT_FEARS = "PATIENT_FEARS"
    CONTRAINDICATION = "CONTRAINDICATION"
    DEFERRED = "DEFERRED"
    JOURNEY_CUT_OFF = "JOURNEY_CUT_OFF"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    OTHER = "OTHER"

class ComorbidCondition(str, Enum):  # independent coexisting diagnoses; extend as found
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

class Demographics(BaseModel):
    gender: str | None = None        # self-reported
    age: int | None = None           # self-reported

class TreatmentRecord(BaseModel):
    name: str
    treatment_class: str
    outcome: TreatmentOutcome
    reason_stopped: str | None = None

class PatientGroundTruth(BaseModel):
    patient_id: str
    to_review: bool = False
    demographics: Demographics = Demographics()   # flat gender/age columns map in here
    churn: bool
    incomplete_journey: bool
    biologic_prescribed: bool
    biologic_taken: bool
    biologic_not_mentioned: bool
    biologic_type: str | None = None
    reasons_for_biologic_prescribed: ReasonPrescribed | None = None
    reasons_for_biologic_not_taken: ReasonNotTaken | None = None
    comorbid_conditions: list[ComorbidCondition] = []
    treatment_records: list[TreatmentRecord] = []
    treatment_outcome: TreatmentOutcome
    referral_pathway: list[str] = []
    evidence_notes: str | None = None
```

## How `v2` is generated

A one-shot transformation cell (read → rename/add/reorder → fill only-empty cells → write)
reads `interviews_ground_truth.ods`, applies the v2 changes, and writes
`interviews_ground_truth_v2.ods`. **It only ever writes into empty cells, so every existing
annotation is preserved**; the original file is untouched. A pandas→`.ods` write carries values
only (dropdowns / frozen header / filters are re-applied in LibreOffice).

## Open questions

- **`churn` meaning** — app vs treatment vs both? (`QUESTIONS.md` #1.)
- **`treatment_outcome`** — acceptable to record `AMBIGUOUS`/`ONGOING`, or force a call?
- **`loss_of_response`** primary vs secondary, + full pathway vocabulary — domain-expert sign-off.
- **Boolean redundancy** — the three `biologic_*` booleans may collapse into one status enum
  (`PRESCRIBED_AND_TAKEN` / `PRESCRIBED_NOT_TAKEN` / `NOT_PRESCRIBED` / `NOT_MENTIONED`) once real
  annotations are in.
- **Balanced gold set ≠ prevalence** — the 20 cases are a balanced *accuracy* set; rate-style
  business answers need the representative full cohort.

## Changelog

- **v0.2** — added `to_review`, `gender`, `age`, `comorbid_conditions`; renamed
  `reasons_for_biologic_denied` → `reasons_for_biologic_not_taken` (enum expanded:
  `INSURANCE_PROBLEMS`, `COST`, `PATIENT_FEARS`); `treatment_outcome` += `AMBIGUOUS`, `ONGOING`;
  reordered (`to_review`/`churn`/`incomplete_journey`/`gender`/`age` after the transcript);
  `evidence_notes` deferred; added `referral_pathway` canonical vocabulary + per-case tooling;
  Pydantic plan updated (`Demographics`, `ReasonNotTaken`, `ComorbidCondition`).
- **v0.1** — initial column set; all annotation columns empty across 50 patients.
