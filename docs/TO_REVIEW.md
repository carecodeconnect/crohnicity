# Cases to review (manual edge-case audit)

A running log of **model-output edge cases** surfaced while verifying each chunked run, for a human
to eyeball against the source transcript in `data/in/interviews_ground_truth_v4.ods`. These are
*judgement calls*, **not schema errors** — schema validity is enforced automatically
(`tests/test_outputs.py`). The point is to catch labels the README's uncertainty handling cares
about — churn, ambiguity, absence — that may be over- or under-flagged.

## Workflow

1. Run a chunk (`uv run python src/main.py --limit=10 --offset=N`); the three checks run — logging
   in `logs/extract.log`, JSON present in `data/out/`, schema validation via `tests/test_outputs.py`.
2. Log any *suspicious-but-valid* prediction in the table below (a defensible-looking record that
   may misread the transcript — e.g. churn on a complete story, a sparse record).
3. Open `interviews_ground_truth_v4.ods`, find the patient, and compare the transcript to the model
   output. Set/keep **`to_review = 1`** to mark it in the validation scope (the split's single
   source of truth — `src/splits.py`).
4. **Fix in the gold annotation** (`_v4.ods`), not the model output: the prediction stays as-is (it
   is what the model said); the gold label is what we score it against.

## Cases

| Patient | Concern | What to check | Status |
|---|---|---|---|
| **P016** | `churn=true` on a fully-populated record (3 treatments, `INSURANCE_PROBLEMS`, full pathway) | Does the transcript actually trail off / cut short? If it reads complete, `churn` is over-flagged. Per README "trustworthiness under churn": a reason drawn from a truncated story is lower-confidence. | ☐ to review |
| **P019** | only 1 treatment record; `before_biologic` count 0 (the lone treatment is the biologic) | Confirm the transcript genuinely mentions no pre-biologic treatments (legit sparse case) vs. the model dropping earlier treatments. | ☐ to review |
| **P049** | **model `churn=false`, but gold `_v4.ods` has `churn=1`** (the `incomplete_journey` merge flagged it) — a model-vs-gold disagreement | Does the transcript look truncated / cut off? If gold is right, the model **under-flagged** churn. Across all 50 the model set `churn=true` only on P016, so churn detection looks under-sensitive — quantify in the EDA. | ☐ to review |
