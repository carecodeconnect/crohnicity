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
