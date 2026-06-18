# Ground-truth annotation schema (v0.1)

This document describes the columns in `data/in/interviews_ground_truth.xlsx`, the
spreadsheet that non-technical stakeholders fill in to create the **gold set** of
labels used to evaluate the extraction pipeline.

> **Status: provisional.** There is no Pydantic schema yet — *this annotation
> exercise is what produces it*. Expect columns, enums, and conventions to change
> as we annotate. When they do, update this file in the same commit so it stays the
> single source of truth. The controlled vocabularies below are mirrored verbatim as
> dropdowns in the spreadsheet; keep the two in sync.

- **File:** `data/in/interviews_ground_truth.xlsx`
- **Sheet:** `ground_truth`
- **Rows:** 50 patients (`P001`–`P050`), one row each
- **Source columns** (`patient_id`, `interview_transcript`) are copied from
  `data/in/interviews.json` and must **not** be edited.
- **Annotation columns** start out empty and are filled by the annotator.

## Columns

| # | Column | Type | Allowed values | Notes |
|---|--------|------|----------------|-------|
| 1 | `patient_id` | `str` | — | Primary key, e.g. `P001`. **Read-only.** |
| 2 | `interview_transcript` | `str` | — | Full interview text. **Read-only** — the evidence you annotate from. |
| 3 | `biologic_prescribed` | `bool` | `TRUE` / `FALSE` | Was a biologic prescribed/recommended to this patient at any point? |
| 4 | `biologic_taken` | `bool` | `TRUE` / `FALSE` | Did the patient actually take/start a biologic? (Prescribed ≠ taken.) |
| 5 | `biologic_not_mentioned` | `bool` | `TRUE` / `FALSE` | `TRUE` when the transcript never raises biologics at all. Distinguishes "explicitly not prescribed" from "topic absent". |
| 6 | `biologic_type` | `str` | free text | Named biologic(s), e.g. `infliximab`, `adalimumab`, `Humira`. Blank if none/unknown. |
| 7 | `reasons_for_biologic_prescribed` | `enum` | `DOCTOR_CHOICE`, `PATIENT_FEARS`, `COST`, `ACCESS`, `OTHER` | Why a biologic *was* the chosen path. |
| 8 | `reasons_for_biologic_denied` | `enum` | `NOT_MENTIONED`, `EXPLICIT_DENIAL`, `JOURNEY_CUT_OFF`, `UNKNOWN`, `OTHER` | Why a biologic was *not* reached. `JOURNEY_CUT_OFF` = transcript ends before the journey resolves. |
| 9 | `churn` | `bool` | `TRUE` / `FALSE` | Did the patient disengage / drop out of care or switch away? (Definition to be tightened during annotation — see Open questions.) |
| 10 | `incomplete_journey` | `bool` | `TRUE` / `FALSE` | `TRUE` when the treatment journey is unresolved in the transcript (recently diagnosed, mid-escalation, lost to follow-up). |
| 11 | `treatment_records` | `list[TreatmentRecord]` (free text for now) | see convention below | All treatments the patient went through, in order. |
| 12 | `treatment_outcome` | `enum` | `SUCCESS`, `FAILED`, `PARTIAL`, `UNKNOWN` | Overall / most-relevant outcome at the patient level. (Per-treatment outcomes live inside `treatment_records`.) |
| 13 | `referral_pathway` | `list[str]` (free text for now) | see convention below | The care journey as ordered steps. |
| 14 | `evidence_notes` | `str` | free text | Supporting snippet(s), rationale per field, and turn references that justify the labels. |

## Controlled vocabularies (dropdown values)

These are enforced as Excel dropdowns. Blanks are allowed (an un-annotated cell).

- **Booleans** (`biologic_prescribed`, `biologic_taken`, `biologic_not_mentioned`, `churn`, `incomplete_journey`): `TRUE`, `FALSE`
- **`reasons_for_biologic_prescribed`**: `DOCTOR_CHOICE`, `PATIENT_FEARS`, `COST`, `ACCESS`, `OTHER`
- **`reasons_for_biologic_denied`**: `NOT_MENTIONED`, `EXPLICIT_DENIAL`, `JOURNEY_CUT_OFF`, `UNKNOWN`, `OTHER`
- **`treatment_outcome`** (and `TreatmentRecord.outcome`): `SUCCESS`, `FAILED`, `PARTIAL`, `UNKNOWN`

## Free-text conventions (until structured)

Excel cells are flat, so the two nested fields use a text convention now and become
proper structured types in the Pydantic model later.

- **`referral_pathway`** — arrow-delimited ordered steps:
  `GP -> misdiagnosis -> specialist_referral -> investigative_surgery -> medication -> medication -> biologic`
- **`treatment_records`** — one treatment per line, pipe-delimited fields in the order
  `name | treatment_class | outcome | reason_stopped`:
  ```
  Prednisone | corticosteroid | FAILED | intolerable side effects
  Azathioprine | immunomodulator | PARTIAL | insufficient response
  Infliximab | biologic | SUCCESS |
  ```

## Toward a Pydantic schema

The columns above sketch the following target model. It is **not implemented yet** —
recorded here so annotation choices map cleanly onto code later.

```python
from enum import Enum
from pydantic import BaseModel

class TreatmentOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"

class ReasonPrescribed(str, Enum):
    DOCTOR_CHOICE = "DOCTOR_CHOICE"
    PATIENT_FEARS = "PATIENT_FEARS"
    COST = "COST"
    ACCESS = "ACCESS"
    OTHER = "OTHER"

class ReasonDenied(str, Enum):
    NOT_MENTIONED = "NOT_MENTIONED"
    EXPLICIT_DENIAL = "EXPLICIT_DENIAL"
    JOURNEY_CUT_OFF = "JOURNEY_CUT_OFF"
    UNKNOWN = "UNKNOWN"
    OTHER = "OTHER"

class TreatmentRecord(BaseModel):
    name: str
    treatment_class: str
    outcome: TreatmentOutcome
    reason_stopped: str | None = None

class PatientGroundTruth(BaseModel):
    patient_id: str
    biologic_prescribed: bool
    biologic_taken: bool
    biologic_not_mentioned: bool
    biologic_type: str | None = None
    reasons_for_biologic_prescribed: ReasonPrescribed | None = None
    reasons_for_biologic_denied: ReasonDenied | None = None
    churn: bool
    incomplete_journey: bool
    treatment_records: list[TreatmentRecord] = []
    treatment_outcome: TreatmentOutcome
    referral_pathway: list[str] = []
    evidence_notes: str | None = None
```

## Open questions (resolve during annotation)

- **`churn` definition** — disengagement from care, switching clinician, or stopping
  treatment against advice? Pin down before inter-annotator agreement matters.
- **`treatment_outcome` vs per-record outcomes** — is the column-level field the
  outcome of the *final* treatment, the *biologic*, or an overall judgement? Decide and
  re-document.
- **One-to-many treatments** — if `treatment_records` gets unwieldy in a single cell,
  promote it to a second sheet keyed by `patient_id`.
- **Boolean redundancy** — `biologic_not_mentioned == TRUE` should imply
  `biologic_prescribed == FALSE`. Consider collapsing the three biologic booleans into
  one status enum (`PRESCRIBED_AND_TAKEN` / `PRESCRIBED_NOT_TAKEN` / `NOT_PRESCRIBED` /
  `NOT_MENTIONED`) once we see real annotations.

## Changelog

- **v0.1** — initial column set seeded from the take-home business questions; all
  annotation columns empty across 50 patients.
