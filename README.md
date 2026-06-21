# Crohnicity: Mama Health Challenge

## Pydantic Schema Design

- Which fields should be **enums** vs. **free text** vs. **structured objects** (e.g., a list of treatment records with name, class, outcome, reason_stopped)?
- How do you distinguish **"not mentioned"** from **"explicitly denied"** from **"cut off before we could find out"**? These are three very different states and they matter for the analysis.
- How do you capture **evidence** — a supporting snippet, turn reference, or rationale per extracted field — so a reviewer can audit the model's decisions?
- Socio-demographic fields: what's worth extracting, what's noise?

## Extraction Pipeline

- **Single-shot vs. multi-stage extraction.** One big call, or a pipeline (e.g., identify-then-extract, or narrative-then-structured)? What are the tradeoffs?
- **Prompt design for uncertainty.** How do you instruct the model to separate absence, negation, and truncation?
- **Determinism and reproducibility.** Temperature, structured output mode, seed, caching — what did you pick and why?

## Evaluation

Pick **one** approach that gives you a real signal on quality. We don't need a rigorous eval harness — we want to see you know how to probe your own pipeline:

1. **Mini golden set:** hand-label 5–10 transcripts yourself on key fields, compute agreement with the model, **or**
2. **LLM-as-judge:** a second LLM call scoring extraction fidelity on a sample against the source transcript, **or**
3. **Consistency check:** run extraction twice (different prompts, temperatures, or models) and use disagreement as a proxy for reliability.

Write up what it told you in a few lines: what the pipeline is solid on, where it's shaky, what you'd fix first with more time.

I picked (1).

## Analysis

A short answer to PharmaCorp's four questions. Numbers with ranges or caveats where sensible. Keep it tight — the point is to demonstrate the structured output is usable, not to write a consulting deck.

1. What percentage of patients in the dataset appear to be on a biologic?
2. For patients *not* on a biologic, what are the primary reasons (doctor choice, patient fears, cost, access, something else)?
3. What other treatments are commonly tried or discussed before a biologic is considered?
4. What does a typical referral pathway look like, in number of steps from GP to a specialist who can prescribe a biologic?

**Churn handling matters here.** Be explicit about:

- How many journeys in your output look truncated vs. complete, and how you decided.
- How you separated "biologic not mentioned" from "biologic discussed and rejected" from "patient churned before reaching that point."
- Which of the four answers are most and least trustworthy given the churn distribution, and why.

### Churn — definition & handling

**Definition.** The spec never defines the "interview". We read it as the patient's interaction
with the Mama Health AI companion app — patients describe their doctors in the *third person*, so
they're narrating *to the app*, not conversing with a clinician. **Churn is therefore
disengagement from that app interaction**, which in the data shows up as a transcript that stops
early. The spec backs this: *"patients disengage partway through their interview — they churn —
leaving us with truncated journeys"*, and the transcripts vary in *"completeness… some cut off
mid-journey"* (with a worked "incomplete, likely churn" example).

**One flag, not two.** Because "churned" and "incomplete journey" are the *same* signal under this
reading, we collapse them into a single `churn` field (ground truth `…_v4.ods` drops
`incomplete_journey`). `churn = true` when there's evidence of **(a)** disengagement from the app
interaction, or **(b)** a truncated / cut-off / vague narrative. Signals: completeness, cut off
mid-journey, truncation, vagueness.

**Why this matters for the answers.** `churn` is the *truncation* state that, with
`biologic_not_mentioned` (absence) and a discussed-but-not-taken biologic (negation), gives the
three-way split the analysis needs — "not mentioned" vs "discussed and rejected" vs "churned
before we could find out". It stays a judgement call with residual uncertainty, but a single
honest flag beats splitting two overlapping ones.

## Evaluation Criteria

- **Schema judgment.** Does your Pydantic model capture the real shape of the problem, including its messiness and uncertainty?
- **Pipeline engineering.** Clean, typed code, sensible error handling, defensible choices on prompting, retries, validation, reproducibility.
- **Uncertainty handling.** Do churn, ambiguity, and absent information show up as first-class signals in your output, or do they silently collapse into nulls?
- **Evaluation mindset.** Do you know whether your pipeline is actually working, and how you know?
- **Communication.** A README where a reader can understand your assumptions, tradeoffs, and limits in under 5 minutes.

We're **not** looking for:
- A perfect extractor — the data is intentionally hard.
- Production-grade architecture.
- A sprawling business-insights writeup.

## Deliverables

A link to your forked, completed GitHub repo containing:

1. Source code in `src/`.
2. Tests in `tests/`.
3. `requirements.txt`.
4. A **`README.md`** with:
   - Your four business answers (brief, with caveats).
   - A pipeline design section — schema choices, prompting approach, error handling, reproducibility.
   - Your evaluation approach and what it surfaced.
   - Churn / limitations discussion.
   - Your "where I used AI" note.

## Optional stretch tasks

Only if you have spare time. We'd rather see a tight core than a bloated stretch:

1. **Multi-stage or chain-of-thought prompts** with inspectable intermediate artifacts.
2. **Confidence scoring per field**, either self-reported by the LLM or derived from consistency across samples.
3. **Open-source model** — swap in a local model (Qwen, Llama, etc.) for one stage via `litellm` and compare quality/latency/cost.
4. **Sankey or pathway visualization** for the referral journey.
5. **Dockerfile** for reproducibility.

I've attempted (4) as a way of answering business question (4) on referral pathways.

## Next Steps

With more time, after the core is complete:

- **Split the single system prompt into multiple focused prompts run concurrently.** This version
  deliberately uses one prompt; a later iteration would break extraction into per-section prompts
  (e.g. biologic funnel, treatment history, referral pathway) run in parallel — better per-field
  accuracy and inspectable intermediate artifacts, at the cost of more calls and orchestration.

## Where I used AI

TBA

## Usage

TBA

## Requirements

Dev environment requirements and setup — Python 3.14 (via uv), a `GEMINI_API_KEY`, and the
VS Code + Claude Code extension diff-review workflow — are documented once in
[docs/SETUP.md](docs/SETUP.md); this README only links there to avoid duplication.

Further documentation is provided as follows:

- [CLAUDE.md](CLAUDE.md) for Claude Code project instructions.

- [SETUP.md](docs/SETUP.md) for installation and usage guide for users and devs.

- [.claude/skills] Agent Skills formatted skills for CC to use specific to this project.