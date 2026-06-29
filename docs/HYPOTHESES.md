# Hypotheses

Provisional answers to the four business questions, from an initial scan (full read of
P001–P010 + a triage scan of P011–P050). These were **hypotheses** — written before the
inference + testing-suite pipeline ran. The **Actual** column is now filled from the completed
50-patient run (model + decoding params: [`config.json`](../config.json); full results &
methodology: [`README.md`](../README.md)).

> **SSOT rule.** The *Actual* cells **link to** the rendered figures in `README.md` and the
> persisted predictions in [`data/out/json/`](../data/out/json) rather than restating literals
> that drift between runs — the README is itself Quarto-rendered from `data/out/`, so each link
> resolves to the latest run. Run-to-run changes are recorded in [`CHANGELOG.md`](../CHANGELOG.md).
> Verified against the run dated in `CHANGELOG.md` [§ 0.1.0](../CHANGELOG.md) (gold
> `interviews_ground_truth_v7.ods` per `config.json`).

| # | Business question | Hypothesis (provisional) | Actual (from latest run) |
|---|---|---|---|
| 1 | What % of patients appear to be on a biologic? | ~**74%** (≈37/50) on / started a biologic; ~26% not. | **Confirmed.** See [README → Q1](../README.md#q1-on-a-biologic) (`biologic_taken == true`, computed in [`src/post_extraction_eda.py`](../src/post_extraction_eda.py) over [`data/out/json/`](../data/out/json)). Gold-eval F1 for the field is in the Q1 table; the headline lands on the hypothesised figure. |
| 2 | For patients *not* on a biologic, primary reasons? | **Insurance/cost dominates** (tier pricing, denials, step-therapy); then "not there yet" (recently diagnosed / mid-workup); then patient fear (needles/side-effects); ≥1 medical contraindication. | **Largely confirmed, with the predicted ordering.** Payer-gating (`INSURANCE_PROBLEMS`) leads, then patient fear (`PATIENT_FEARS`) and `COST`, then "not there yet" (`DEFERRED`, e.g. [P048](../data/out/json/P048.json) deferred post-surgery) and `CONTRAINDICATION` — see [README → Q2](../README.md#q2--reasons-not-on-a-biologic) and the enum [`ReasonNotTaken`](../src/schema.py). Note: the enum is `INSURANCE_PROBLEMS` not bare "access" (rationale in [`docs/SCHEMA.md`](SCHEMA.md)); reasons are **multi-select**. |
| 3 | Treatments tried/discussed before a biologic? | Step-up ladder: aminosalicylates (mesalamine, sulfasalazine) → corticosteroids (prednisone, budesonide) → immunomodulators/thiopurines (azathioprine, 6-MP) / methotrexate; surgery for complications. | **Confirmed (the classic step-up ladder).** Ranked `treatment_class` counts put 5-ASA → corticosteroid → immunomodulator at the top — see [README → Q3](../README.md#q3--treatments-tried-before-a-biologic) (counts over `treatment_records` where `biologic_timing == BEFORE`, enum [`BiologicTiming`](../src/schema.py)). **Caveat (still open):** free-text `treatment_class` is un-normalised, and the count also includes earlier *biologics* (a switch vs. a mislabel) — see the Q3 error-handling note in the README. |
| 4 | Typical referral pathway (steps GP → biologic prescriber)? | ~1 formal referral (GP → gastroenterologist), but commonly preceded by an initial misdiagnosis (IBS/stress) + wait; colonoscopy confirms; biologic after conventional therapy fails. | **Partially confirmed; the "1 referral" framing did not survive.** The misdiagnosis-then-confirmation-then-biologic arc holds, but the literal "GP → prescriber" step count does **not**: the GP node (`primary_care_contact`) is under-emitted, so steps are counted from journey start to `biologic_recommended` — modal/median length and the cyclic-journey finding are in [README → Q4](../README.md#q4-referral-pathway-length-steps-to-a-biologic-prescribing-specialist) (`PathwayStep` enum in [`src/schema.py`](../src/schema.py)). |

## Hypotheses still genuinely untested

These were implied by the scan but are **not** resolved by the current pipeline — kept open:

- **Initial misdiagnosis is the norm (IBS/stress before Crohn's).** The pathway data shows a
  `misdiagnosis` step on many journeys, but its *rate* across the cohort was never measured as a
  hypothesis test — only surfaced incidentally in the Q4 phase/transition tables
  ([`src/referral_pathway_analysis.py`](../src/referral_pathway_analysis.py)). **Untested.**
- **Cost/insurance reasons co-occur with fear (multiple reasons per patient).** The schema makes
  `reasons_for_biologic_not_taken` multi-select, so co-occurrence is *representable*, but the
  co-occurrence rate was not computed. **Untested** (would need a cross-tab over `data/out/json/`).
- **Demographic skew in pathway/outcome.** `Demographics{gender, age}` is extracted to enable a
  later "do pathways/outcomes differ by demographic" cut (README → *Pydantic Schema Design*), but
  that cut was deferred. **Untested.**
- **Churn / truncation rate.** The hypothesis scan flagged "some transcripts cut off mid-journey."
  The model's `churn` flag (see [README → Churn](../README.md#churn-definition-handling)) is
  known-unreliable in both directions (gold audit: [`docs/TO_REVIEW.md`](TO_REVIEW.md)), so the
  *true* truncation rate remains **untested** pending a deterministic tail-of-text rule
  ([`docs/TODO.md`](TODO.md)).

Basis for the hypotheses: indicative counts from the manual scan, not the validated pipeline. The
*Actual* column and the open list above are kept honest by linking to the SSOT (`README.md` /
`data/out/` / `config.json` / `src/schema.py`) rather than copying figures that drift.
