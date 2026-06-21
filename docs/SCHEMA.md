# Ground-truth annotation schema (v0.4)

Columns in the ground-truth spreadsheet that stakeholders fill in to create the **gold set**
of labels for evaluating the extraction pipeline.

> **Status: provisional.** This annotation exercise is what produces the Pydantic schema —
> expect change. Controlled vocabularies below are the single source of truth; mirror them as
> spreadsheet dropdowns. Open business questions live in `docs/QUESTIONS.md`; the pathway
> vocabulary needs domain-expert sign-off (`docs/TODO.md`).

- **Working file:** `data/in/interviews_ground_truth_v5.ods`, built from the annotated
  `interviews_ground_truth.ods` → `_v2` → `_v3` → `_v4` → `_v5` by `sandbox/build_ground_truth_v*.py` (see
  "How the working file is generated").
- **Rows:** 50 patients (`P001`–`P050`); 20 reviewed so far (`to_review == 1`).
- **Source columns** (`patient_id`, `interview_transcript`) come from `interviews.json` — **do not edit**.
- **Note:** booleans persist in the `.ods` as `1`/`0` (incl. `to_review`, now standardised), blanks as empty.

## Columns (17, in sheet order)

| # | Column | Type | Allowed values | Notes |
|---|--------|------|----------------|-------|
| 1 | `patient_id` | `str` | — | Primary key. **Read-only.** |
| 2 | `interview_transcript` | `str` | — | Full interview text. **Read-only.** |
| 3 | `to_review` | `bool` (1/0) | `1`/`0` | `1` = case is in the annotation scope; filter on this. Single source of truth for the validation/holdout split (`src/splits.py`). |
| 4 | `churn` | `bool` (1/0) | `1`/`0` | `1` = interview truncated / patient disengaged before the story resolved (cut off, trails off, vague). **Merges the old `incomplete_journey`** (v4). See README "Churn" / `QUESTIONS.md` #1. |
| 5 | `gender` | `str` | free text | Self-reported (`female`/`male` as stated) → `Demographics`. |
| 6 | `age` | `int` | — | Self-reported → `Demographics`. |
| 7 | `biologic_prescribed` | `bool` (1/0) | `1`/`0` | Was a biologic prescribed/recommended at any point? (recommend vs prescribe — `QUESTIONS.md` #5.) |
| 8 | `biologic_taken` | `bool` (1/0) | `1`/`0` | Did the patient actually start/take one? (Prescribed ≠ taken.) |
| 9 | `biologic_not_mentioned` | `bool` (1/0) | `1`/`0` | `1` when biologics never come up at all. |
| 10 | `biologic_type` | `str` | free text | Named biologic(s), e.g. `Humira`, `infliximab`. |
| 11 | `reasons_for_biologic_prescribed` | `enum` | see vocab | Why a biologic *was* the chosen path. |
| 12 | `reasons_for_biologic_not_taken` | `enum` | see vocab | Renamed from `reasons_for_biologic_denied`. Why a prescribed biologic wasn't taken / wasn't reached. |
| 13 | `comorbid_conditions` | `list[enum]` | see vocab | Independent coexisting diagnoses (not Crohn's sequelae). Comma-separated. |
| 14 | `treatment_records` | `list[TreatmentRecord]` (free text) | see convention | All treatments, in order. Each carries `before_biologic` (the before/after split for Q3). |
| 15 | `treatment_outcome` | `enum` | see vocab | Overall patient-level outcome; `AMBIGUOUS`/`ONGOING` allowed (confirmed). |
| 16 | `referral_pathway` | `list[str]` (free text) | see convention | Canonical-event journey chain. |
| 17 | `evidence_notes` | `str` | free text | **DEFERRED** — kept as a column, not yet populated; also the destination for any prose mis-entered into other fields. |

## Controlled vocabularies

- **Booleans** (`to_review`, `churn`, `biologic_prescribed`, `biologic_taken`, `biologic_not_mentioned`): `1` / `0` (stored numeric in the `.ods`).
- **`reasons_for_biologic_prescribed`**: `DOCTOR_CHOICE`, `PATIENT_FEARS`, `COST`, `ACCESS`, `NOT_APPLICABLE`, `OTHER`
- **`reasons_for_biologic_not_taken`**: `NOT_MENTIONED`, `EXPLICIT_DENIAL`, `INSURANCE_PROBLEMS`, `COST`, `PATIENT_FEARS`, `CONTRAINDICATION`, `DEFERRED`, `JOURNEY_CUT_OFF`, `UNKNOWN`, `NOT_APPLICABLE`, `OTHER`
  - *`CONTRAINDICATION` = medically can't be given (e.g. COPD risk); `DEFERRED` = appropriate but postponed (awaiting surgery recovery / timing).*
  - *`NOT_APPLICABLE` (in both reasons enums) = the field genuinely doesn't apply (no biologic prescribed, or it was taken) — distinct from a blank cell, which means "not yet annotated".*
  - *(`PATIENT_FEARS` belongs here — fear of needles/side-effects is a reason a biologic isn't taken, not prescribed. `INSURANCE_PROBLEMS` = denial/auth/tier; `COST` = affordability even when covered.)*
- **`treatment_outcome`** (and `TreatmentRecord.outcome`): `SUCCESS`, `FAILED`, `PARTIAL`, `AMBIGUOUS`, `ONGOING`, `UNKNOWN`
  - *(`AMBIGUOUS` = stated but mixed/contradictory; `ONGOING` = unresolved/still escalating; `UNKNOWN` = not stated.)*
- **`comorbid_conditions`** (seeded from P001–P050; extend as found): `TYPE_2_DIABETES`, `HYPERTENSION`, `HYPERLIPIDEMIA`, `ANXIETY_DISORDER`, `DEPRESSION`, `PCOS`, `ENDOMETRIOSIS`, `MIGRAINE`, `HYPOTHYROIDISM`, `FIBROMYALGIA`, `ASTHMA`, `RHEUMATOID_ARTHRITIS`, `ADHD`, `SLEEP_APNEA`, `OTHER`
  - *Excludes Crohn's-driven sequelae (psoriasis, osteoporosis, anemia, short-bowel, enteropathic arthritis) — those are treatment/disease effects, not independent risk factors.*
  - *Several real diagnoses have no clean token yet (bipolar, heart disease, COPD, PSC/autoimmune hepatitis, insulin resistance, eating disorder) — see Open questions.*

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

class PatientLabels(BaseModel):
    patient_id: str
    to_review: bool = False
    demographics: Demographics = Demographics()   # flat gender/age columns map in here
    churn: bool | None = None             # truncation/disengagement; merges incomplete_journey (v4)
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

## How the working file is generated

Two one-shot scripts in `sandbox/` (kept as a reviewable record):

1. `build_ground_truth_v2.py` — `interviews_ground_truth.ods` → `_v2`: rename/add/reorder
   columns, bootstrap `to_review`, fill empty `referral_pathway`/`gender`/`age` candidates.
2. `build_ground_truth_v3.py` — `_v2` → `_v3`: standardise `to_review` to `1`/`0`, and move any
   prose mis-entered in the reasons columns into `evidence_notes`.

Both **only write into empty cells, so existing annotations are preserved**, and both write the
`.ods` with column widths + an autofilter via `odfpy` (the frozen header is the one manual step:
**View ▸ Freeze Rows**). The original `.ods` is never modified.

## Open questions

- **`churn` definition (resolved for this version)** — `churn` = the interview is truncated /
  the patient disengaged before the story resolved (reading the "interview" as the patient's
  interaction with the Mama Health app). The old `incomplete_journey` is **merged into `churn`**
  (v4) — same truncation signal, one flag. Still a judgement call; CAIO confirmation welcome
  (`QUESTIONS.md` #1).
- **`comorbid_conditions` token gaps** — bipolar, heart disease, COPD, PSC + autoimmune
  hepatitis, insulin resistance, eating disorder have no canonical token. Map to `OTHER`, or
  extend the enum?
- **`loss_of_response`** primary vs secondary, + full pathway vocabulary — domain-expert sign-off.
- **Biologic funnel** — the three `biologic_*` booleans may collapse into one status enum
  (`PRESCRIBED_AND_TAKEN` / `PRESCRIBED_NOT_TAKEN` / `NOT_PRESCRIBED` / `NOT_MENTIONED`); relatedly,
  a separate `biologic_recommended` step (recommend → prescribe → taken) is under consideration
  (`QUESTIONS.md` #5).
- **Balanced gold set ≠ prevalence** — the 20 are a balanced *accuracy* set; rate-style business
  answers need the representative full cohort.

*Resolved:* `treatment_outcome` may record `AMBIGUOUS`/`ONGOING` (confirmed — no forced
SUCCESS/FAILED call).

## Changelog

- **v0.4** — **`incomplete_journey` merged into `churn` and dropped** (working file `_v4.ods`).
  *Why:* reading the "interview" as the patient's interaction with the Mama Health app, `churn`
  (app disengagement) and `incomplete_journey` (truncated transcript) are the **same signal**, so
  one honest flag beats two overlapping ones (see README "Churn"). `churn` is therefore defined
  (interview truncated / patient disengaged), no longer "pending CAIO". `TreatmentRecord` gained
  `before_biologic` (the before/after split for Q3). `PatientLabels` is now implemented in
  `src/schema.py`; the system prompt lives in `data/prompts/system.txt`.
- **v0.3** — `reasons_for_biologic_not_taken` += `CONTRAINDICATION`, `DEFERRED`; both reasons enums
  += `NOT_APPLICABLE`; `to_review` standardised to `1`/`0`; working file is now `_v3.ods` (built
  via the `sandbox/` scripts; prose moved from reasons → `evidence_notes`); `treatment_outcome`
  `AMBIGUOUS`/`ONGOING` confirmed acceptable; `churn`/`incomplete_journey` definitions narrowed
  (app-disengagement / record-incomplete) and recorded `0` across the reviewed 20 pending CAIO;
  20/50 cases reviewed.
- **v0.2** — added `to_review`, `gender`, `age`, `comorbid_conditions`; renamed
  `reasons_for_biologic_denied` → `reasons_for_biologic_not_taken` (enum expanded:
  `INSURANCE_PROBLEMS`, `COST`, `PATIENT_FEARS`); `treatment_outcome` += `AMBIGUOUS`, `ONGOING`;
  reordered (`to_review`/`churn`/`incomplete_journey`/`gender`/`age` after the transcript);
  `evidence_notes` deferred; added `referral_pathway` canonical vocabulary + per-case tooling;
  Pydantic plan updated (`Demographics`, `ReasonNotTaken`, `ComorbidCondition`).
- **v0.1** — initial column set; all annotation columns empty across 50 patients.

