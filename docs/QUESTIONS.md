# Outstanding questions for the CAIO

Business / product-level questions needing a stakeholder decision before the matching schema
fields and metrics can be finalised. (Clinical/coding questions for a domain expert are
tracked separately as the domain-expert item in `docs/TODO.md`.)

## 1. What does "churn" mean?

- **From the app?** — a user disengages from / stops using the Mama Health product.
- **From treatment?** — a patient disengages from medical care (stops treatment, lost to
  follow-up, abandons a clinician).
- **Both / something else?**

This decides how `churn` is annotated and what it can measure. From the data review: genuine
*treatment* disengagement is rare and rarely explicit in the transcripts (~1 clear case in
P001–P050). If "churn" means *app* churn, the interview transcripts likely don't contain the
signal at all — we'd need product/usage data instead.

**Spec hint (README):** *"Some patients disengage partway through their interview — they churn —
leaving us with truncated journeys."* This frames churn as **disengaging partway through the
interview itself** (a truncated transcript) — closer to our `incomplete_journey` notion (Q4) than
to app/treatment churn.

**Decision (v4):** we read the "interview" as the patient's interaction with the Mama Health app
(patients describe their doctors in the *third person*, so they're narrating to the app, not a
clinician). So `churn` = disengagement from that interaction, which surfaces as a **truncated
transcript**. Because that is the *same* signal as `incomplete_journey`, the two are **merged into
a single `churn` flag** (`incomplete_journey` dropped in v4) — one honest flag beats two
overlapping ones. See README "Churn"; CAIO confirmation still welcome.

## 2. What is the source of the interview transcripts?

- How were the `interview_transcript` texts produced — real patient interviews, clinician
  notes, synthetic / LLM-generated, or a mix?
- This affects how much extracted detail we can trust and what biases to expect.

**Partly answered (README):** the transcripts are **synthetic** ("50 synthetic interview
transcripts"), and patient stories are **collected longitudinally**, with some patients
disengaging partway. Still open: *how* the interviews are administered/collected (self-report,
clinician-led, app-based?) and what the synthetic generator modelled.

## 3. Definitions of the key outcome variables — we need a data dictionary

- Authoritative definitions of the key outcome variables, **especially `churn`** (see Q1),
  plus `biologic_taken` vs `biologic_prescribed`, and `treatment_outcome`. (`incomplete_journey`
  is now merged into `churn` — see Q1/Q4.)
- A short **data dictionary** (term → definition → how to decide it from a transcript) so
  annotation and metrics stay consistent and defensible.

## 4. What does "incomplete_journey" mean?

> **Resolved (v4):** `incomplete_journey` has been **merged into `churn`** and dropped as a separate
> field. Under the app-interaction reading of "interview" (Q1), a truncated transcript *is* churn —
> the same signal — so two overlapping flags added noise, not precision. Question retained for
> context. See README "Churn".

- Where's the boundary? Some cases reach an apparent endpoint yet were flagged incomplete
  (e.g. **P045**), so the criterion is unclear — does "incomplete" mean the transcript cuts off
  mid-journey, the patient hasn't yet reached a biologic / resolution, or something else?
- Needs a precise rule, **and how it differs from `churn`**, so the flag is applied consistently.

## 5. What does "biologic_prescribed" mean — prescribed vs recommended?

- A clinician can *recommend / suggest* a biologic without a prescription ever being written.
  Does `biologic_prescribed` mean an actual prescription, or any recommendation?
- Do we need a separate **`biologic_recommended`** column to capture that step
  (recommended → prescribed → taken)? This depends on the business context — confirm whether the
  recommend-vs-prescribe distinction matters for the four questions.

## 6. Biologic detection depends on knowing the brand names

Not every transcript says "biologic" — many only name a branded drug (e.g. *Humira*, *Remicade*,
*Stelara*, *Entyvio*). Without a known list of biologic names, it wasn't always possible to spot
whether a biologic was used, so some `biologic_*` labels may be unreliable. We need an
authoritative list of biologic **brand + generic** names to detect/normalise reliably (relates to
the branded-biologics registry in `docs/TODO.md`).

## 7. PII / GDPR handling for production data

The current `data/in/interviews.json` looks **synthetic**, so it's kept in the (private) repo.
Before any **real** patient data enters the pipeline we need a decision on:

- Is the production interview data **personal data** under GDPR (likely special-category health
  data)? If so it must not sit in git or in `data/out/` artefacts.
- Lawful basis, retention period, and **de-identification / pseudonymisation** before transcripts
  are sent to an external LLM (Gemini).
- Where production inputs/outputs should live (secure storage, not version control), and what the
  **data-processing agreement** with the model provider must cover.

## 8. What aggregation levels does the business need?

The four README questions are mostly **by patient** (% on a biologic, reasons for not being on
one, referral steps) with some **by treatment** (treatments tried before a biologic). Future
analytics may need other grains — **by medication/biologic**, **by comorbid condition**, by
demographic, or by journey-type. Confirm the required aggregation levels so the schema and outputs
support them. For version-controlled, scalable platform analytics, consider **dbt SQL models** over
the structured output (one transformation layer per grain) rather than ad-hoc pandas.
