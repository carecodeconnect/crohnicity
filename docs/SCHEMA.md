# Ground-truth annotation schema (v0.8)

Columns in the ground-truth spreadsheet that stakeholders fill in to create the **gold set**
of labels for evaluating the extraction pipeline.

> **Status: provisional.** This annotation exercise is what produces the Pydantic schema —
> expect change. Controlled vocabularies below are the single source of truth; mirror them as
> spreadsheet dropdowns. Open business questions live in `docs/QUESTIONS.md`; the pathway
> vocabulary needs domain-expert sign-off (`docs/TODO.md`).

- **Two version numbers, on purpose:** the **schema version** (`v0.8` — this doc's changelog below)
  tracks the *vocabulary/fields* (live source: [`src/schema.py`](../src/schema.py)); the **gold-file
  version** (`_v7` — [`config.json`](../config.json) `gold`) tracks the *data file* (rebuilt by
  `sandbox/build_ground_truth_v*.py`). They are independent counters whose latest entries
  **correspond** — the `v0.8` change (`BIOLOGIC_TAKEN`) is what produced `_v7.ods` — but the numbers
  differ because each artefact has been revised a different number of times.
- **Working file:** `data/in/interviews_ground_truth_v7.ods`, built from the annotated
  `interviews_ground_truth.ods` → `_v2` → `_v3` → `_v4` → `_v5` → `_v6` → `_v7` by `sandbox/build_ground_truth_v*.py` (see
  "How the working file is generated").
- **Rows:** 50 patients (`P001`–`P050`); 21 reviewed so far (`to_review == 1`).
- **Source columns** (`patient_id`, `interview_transcript`) come from `interviews.json` — **do not edit**.
- **Note:** booleans persist in the `.ods` as `1`/`0` (incl. `to_review`, now standardised), blanks as empty.

## Columns (17, in sheet order)

| # | Column | Type | Allowed values | Notes |
|---|--------|------|----------------|-------|
| 1 | `patient_id` | `str` | — | Primary key. **Read-only.** |
| 2 | `interview_transcript` | `str` | — | Full interview text. **Read-only.** |
| 3 | `to_review` | `bool` (1/0) | `1`/`0` | `1` = case is in the annotation scope; filter on this. Single source of truth for which cases `gold_eval` scores against the gold. |
| 4 | `churn` | `bool` (1/0) | `1`/`0` | `1` = interview truncated / patient disengaged before the story resolved (cut off, trails off, vague). **Merges the old `incomplete_journey`** (v4). See SOLUTION "Churn" / `QUESTIONS.md` #1. |
| 5 | `gender` | `str` | free text | Self-reported (`female`/`male` as stated) → `Demographics`. |
| 6 | `age` | `int` | — | Self-reported → `Demographics`. |
| 7 | `biologic_prescribed` | `bool` (1/0) | `1`/`0` | Was a biologic prescribed/recommended at any point? (recommend vs prescribe — `QUESTIONS.md` #5.) |
| 8 | `biologic_taken` | `bool` (1/0) | `1`/`0` | Did the patient actually start/take one? (Prescribed ≠ taken.) |
| 9 | `biologic_not_mentioned` | `bool` (1/0) | `1`/`0` | `1` when biologics never come up at all. |
| 10 | `biologic_type` | `str` | free text | Named biologic(s), e.g. `Humira`, `infliximab`. |
| 11 | `reasons_for_biologic_prescribed` | `enum` | see vocab | Why a biologic *was* the chosen path. |
| 12 | `reasons_for_biologic_not_taken` | `list[enum]` | see vocab | Renamed from `reasons_for_biologic_denied`. Why a prescribed biologic wasn't taken / wasn't reached. **Multiple allowed** (primary first) — patients often have several (e.g. cost + fear). |
| 13 | `comorbid_conditions` | `list[enum]` | see vocab | Independent coexisting diagnoses (not Crohn's sequelae). Comma-separated. |
| 14 | `treatment_records` | `list[TreatmentRecord]` (free text) | see convention | All treatments, in order. Each carries `biologic_timing` (the before/after split for Q3). |
| 15 | `treatment_outcome` | `enum` | see vocab | Overall patient-level outcome; `AMBIGUOUS`/`ONGOING` allowed (confirmed). |
| 16 | `referral_pathway` | `list[str]` (free text) | see convention | Canonical-event journey chain. |
| 17 | `evidence_notes` | `str` | free text | **DEFERRED** — kept as a column, not yet populated; also the destination for any prose mis-entered into other fields. |

## Controlled vocabularies

- **Booleans** (`to_review`, `churn`, `biologic_prescribed`, `biologic_taken`, `biologic_not_mentioned`): `1` / `0` (stored numeric in the `.ods`).
- **`reasons_for_biologic_prescribed`** (single — the *initiation* signal): `DOCTOR_CHOICE`, `PATIENT_REQUEST`, `NOT_APPLICABLE`, `OTHER`. Trimmed: `COST`/`PATIENT_FEARS`/`ACCESS` removed (those are reasons a biologic is **not taken**, not reasons it was prescribed; `ACCESS` had zero transcript support — covered by `COST` + `INSURANCE_PROBLEMS`).
- **`reasons_for_biologic_not_taken`** (list — **multiple allowed**, primary first; **never empty**): `NOT_MENTIONED`, `EXPLICIT_DENIAL`, `INSURANCE_PROBLEMS`, `COST`, `PATIENT_FEARS`, `CONTRAINDICATION`, `DEFERRED`, `UNKNOWN`, `BIOLOGIC_TAKEN`, `NOT_APPLICABLE`, `OTHER`
  - *`CONTRAINDICATION` = medically can't be given (e.g. COPD risk); `DEFERRED` = appropriate but postponed (awaiting surgery recovery / timing).*
  - *Non-reason states keep the list explicit (**never empty**, so it's never confused with a missing value): `BIOLOGIC_TAKEN` = a biologic was taken; `NOT_APPLICABLE` = none was ever prescribed/offered; `NOT_MENTIONED` = biologics never come up; `UNKNOWN` = prescribed-but-not-taken, no reason. (`ReasonPrescribed.NOT_APPLICABLE` likewise = no biologic prescribed.) A blank cell still means "not yet annotated".*
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

## The Pydantic schema

The schema is **defined once** in [`src/schema.py`](../src/schema.py) — the single source of truth,
enum-validated at the model boundary (`enforce_validation`). It is **not duplicated here** (DRY):
read it there, or browse the rendered API reference (`uv run mkdocs serve` → *Source (src/)*) for
each model's field docstrings. The `*Enum` classes there (`TreatmentOutcome`, `ReasonPrescribed`,
`ReasonNotTaken`, `ComorbidCondition`, `BiologicTiming`) are the controlled vocabularies to mirror
as spreadsheet dropdowns; the rationale for each change is in the Changelog below.

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
  interaction with the app). The old `incomplete_journey` is **merged into `churn`**
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

- **v0.8** — **`BIOLOGIC_TAKEN` added to `ReasonNotTaken`; the list is now never empty.** The model
  was returning `[]` for patients *on* a biologic, which is indistinguishable from a missing value
  (can't tell "taken, N/A" from "not taken, no reason found"). An explicit `[BIOLOGIC_TAKEN]` —
  alongside `[NOT_MENTIONED]` / `[NOT_APPLICABLE]` / `[UNKNOWN]` — keeps the field trackable.
  `NOT_APPLICABLE` now means specifically "no biologic ever prescribed/offered" (the "taken"
  meaning moved to `BIOLOGIC_TAKEN`).
- **v0.7** — **Reason enums realigned to the business spec (`TASK_INSTRUCTIONS.md` Q2), evidence
  from all 50 transcripts.** `ReasonPrescribed` trimmed to the *initiation* signal
  `{DOCTOR_CHOICE, PATIENT_REQUEST, NOT_APPLICABLE, OTHER}` — `COST`/`PATIENT_FEARS`/`ACCESS`
  removed (they're reasons a biologic is *not taken*, not reasons prescribed; `ACCESS` had **zero**
  transcript support — every "can't get it" is `COST` or `INSURANCE_PROBLEMS`). **`reasons_for_biologic_not_taken`
  is now a list** (`list[ReasonNotTaken]`, primary first) because patients often have several
  reasons (e.g. cost + fear). Gold off-vocab (`NOT PRESCRIBED` / `NOT MENTIONED` / `BIOLOGIC WAS
  TAKEN`) normalised to `NOT_APPLICABLE` / `NOT_MENTIONED` in the `_v6` rebuild.
- **v0.6** — **`JOURNEY_CUT_OFF` dropped from `ReasonNotTaken`.** *Why:* "not taken because the
  journey was cut off" is the same truncation signal `churn` already carries, so it duplicated
  `churn` (cf. the v0.4 `incomplete_journey` → `churn` merge). A cut-off case is now `churn = 1`
  with `reasons_for_biologic_not_taken = UNKNOWN`. Working file bumped to `_v6.ods` — P047 completed
  as a reviewed gold case.
- **v0.5** — **`TreatmentRecord.before_biologic` (`bool | None`) replaced by `biologic_timing`
  (`BiologicTiming` enum: `BEFORE` / `LATER` / `NO_BIOLOGIC` / `UNKNOWN`).** *Why:* the old `null`
  was overloaded — it meant both "no biologic exists to anchor the split" and "ordering unclear";
  the enum makes each state explicit and is enum-validated at the model boundary like the other
  controlled vocabularies. Q3 now counts `biologic_timing == "BEFORE"` (same set as the old
  `before_biologic == true`). Takes effect on the next fresh extraction run.
- **v0.4** — **`incomplete_journey` merged into `churn` and dropped** (working file `_v4.ods`).
  *Why:* reading the "interview" as the patient's interaction with the app, `churn`
  (app disengagement) and `incomplete_journey` (truncated transcript) are the **same signal**, so
  one honest flag beats two overlapping ones (see SOLUTION "Churn"). `churn` is therefore defined
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

