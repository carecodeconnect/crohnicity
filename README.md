# Chronicity: Mama Health Challenge

1. Your four business answers (brief, with caveats).
2. A pipeline design section — schema choices, prompting approach, error handling, reproducibility.
3. Your evaluation approach and what it surfaced.
4. Churn / limitations discussion.
5. Your "where I used AI" note.


## The Business Context 🎯

A major pharma company, "PharmaCorp," is preparing to launch a new biologic for **Crohn's Disease**, a chronic inflammatory bowel disease. Biologics are powerful but expensive, and have notable side effects. PharmaCorp's commercial team needs to understand the treatment landscape their drug will enter — especially for patients with moderate-to-severe Crohn's who are **not yet on a biologic**.

We collect patient stories longitudinally, but not all of them are complete. Some patients disengage partway through their interview — they **churn** — leaving us with truncated journeys. This is a real operational constraint, and your pipeline needs to handle it honestly rather than pretending it isn't there.

**PharmaCorp's questions:**

1. What percentage of patients in the dataset appear to be on a biologic?
2. For patients *not* on a biologic, what are the primary reasons (doctor choice, patient fears, cost, access, something else)?
3. What other treatments are commonly tried or discussed before a biologic is considered?
4. What does a typical referral pathway look like, in number of steps from GP to a specialist who can prescribe a biologic?

---

## Your Mission 🚀

Build an **LLM-based extraction pipeline** that turns 50 synthetic interview transcripts into structured records, with quality and uncertainty signals rich enough that a downstream analyst could trust the output. Then use that output to answer PharmaCorp's questions.

The pipeline is the centerpiece. The analysis is the sanity check that your output is actually useful.


## Requirements

Dev environment requirements and setup — Python 3.14 (via uv), a `GEMINI_API_KEY`, and the
VS Code + Claude Code extension diff-review workflow — are documented once in
[docs/SETUP.md](docs/SETUP.md); this README only links there to avoid duplication.

Further documentation is provided as follows:

- [CLAUDE.md](CLAUDE.md) for Claude Code project instructions.

- [SETUP.md](docs/SETUP.md) for installation and usage guide for users and devs.

- [.claude/skills] Agent Skills formatted skills for CC to use specific to this project.