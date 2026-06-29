# Cases to review (manual edge-case audit)

A running log of **model-output edge cases** surfaced while verifying each chunked run, for a human
to eyeball against the source transcript in `data/in/interviews_ground_truth_v6.ods`. These are
*judgement calls*, **not schema errors** — schema validity is enforced automatically
(`tests/test_outputs.py`). The point is to catch labels the README's uncertainty handling cares
about — churn, ambiguity, absence — that may be over- or under-flagged.

## Churn audit summary (reviewed cases)

Model `churn` predictions vs. human judgement on the flagged cases:

| Case | Model | Reviewed | Outcome |
|---|---|---|---|
| P016 | `true`  | not churn | **false positive** (stylistic "…", complete ending) |
| P019 | `false` | not churn | **true negative** |
| P049 | `false` | **churn** | **false negative** (mid-word "Chronic…", no prior "…") |

**Verdict:** churn detection is unreliable in both directions — the model got both *hard* cases
wrong (FP + FN) and only the easy one right. Churn (= truncation / app-disengagement) is largely a
**lexical/structural** signal here (how the transcript *ends*), under-determined by the narrative —
better suited to a deterministic tail-of-text rule than the extraction prompt. Quantify in the EDA.

## Workflow

1. Run a chunk (`uv run python src/main.py --limit=10 --offset=N`); the three checks run — logging
   in `logs/extract.log`, JSON present in `data/out/`, schema validation via `tests/test_outputs.py`.
2. Log any *suspicious-but-valid* prediction in the table below (a defensible-looking record that
   may misread the transcript — e.g. churn on a complete story, a sparse record).
3. Open `interviews_ground_truth_v6.ods`, find the patient, and compare the transcript to the model
   output. Set/keep **`to_review = 1`** to mark it in the gold-annotation scope (the cases
   `gold_eval` scores).
4. **Fix in the gold annotation** (`_v6.ods`), not the model output: the prediction stays as-is (it
   is what the model said); the gold label is what we score it against.

## Cases

| Patient | Concern | What to check | Status |
|---|---|---|---|
| **P016** | `churn=true` on a fully-populated record (3 treatments, `INSURANCE_PROBLEMS`, full pathway) | Does the transcript actually trail off / cut short? | **☑ Reviewed → NOT churn (model over-flagged).** The trailing `"..."` reads as a stylistic "continued"/emotional marker, and the final line (*"…anything would be better than this…"*) reads as an ending sentence, not a cut-off. Not enough evidence to call "disengaged from app" without further signals. Gold `churn = 0`. |
| **P019** | only 1 treatment record; `biologic_timing == BEFORE` count 0 (the lone treatment is the biologic) | Confirm the transcript genuinely mentions no pre-biologic treatments (legit sparse case) vs. the model dropping earlier treatments. | **☑ Reviewed → NOT churn.** Transcript is detailed/engaged; final line (*"But at 24, that's a lot of days ahead"*) reads as an ending, not a mid-stream cut-off. Model already had `churn=false` — **agrees** (true negative). |
| **P049** | **model `churn=false`, but gold `_v6.ods` has `churn=1`** (the `incomplete_journey` merge flagged it) — a model-vs-gold disagreement | Does the transcript look truncated / cut off? If gold is right, the model **under-flagged** churn. | **☑ Reviewed → IS churn (model under-flagged → false negative).** Genuine truncation: the transcript ends mid-sentence on the first word (*"Chronic…"*), and — unlike P016 — there are **no prior "…" markers**, so the trailing "…" is a real cut-off, not a stylistic habit. Confirms gold `churn = 1`. |

**`to_review` flag status in `_v6.ods`** (filter `to_review = 1` to see the review set): **P016 ✓**
and **P049 ✓** are already flagged — they're in the 20-case review set. **P019 is `to_review = 0`**
— set it to `1` in LibreOffice if you want it to surface alongside the others. Flagging P019 would
add this edge case to the gold-annotation scope (21 cases).
