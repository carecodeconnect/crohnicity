# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python (chronicity)
#     language: python
#     name: chronicity
# ---

# %% [markdown]
# # 03 — Extraction test
#
# A thin frontend to `src/extract.py` for **visually inspecting** the structured output of a
# single live Gemini call, before wiring up the full `data/in/interviews.json` loop.
#
# > **This notebook always makes a real Gemini API call** when you run the cells below.
# > `RUN_LIVE_TESTS` does **not** apply here — that flag only gates the live *pytest* in
# > `tests/test_extract.py`, never `extract()`. A `503 … high demand` error just means Gemini was
# > temporarily busy; rerun shortly.
#
# Run one transcript through `extract()` and print the resulting `PatientLabels` as indented
# JSON, so every field (enums, demographics, `referral_pathway`, …) can be checked by eye.
#
# `extract()` loads `GEMINI_API_KEY` from `.env` itself — no extra setup needed.

# %%
import logging
import sys

import litellm

sys.path.append("../src")  # kernel cwd is notebooks/ (per %pwd); src/ is one level up

from extract import LOG_DIR, TESTS_OUT, extract

litellm._turn_on_debug()  # verbose LiteLLM logging for debugging API calls (e.g. 503s)

# litellm logs via the stdlib `logging` module (not loguru); attach a file handler to the
# "LiteLLM" logger so the verbose debug stream persists to logs/litellm_debug.log.
logging.getLogger("LiteLLM").addHandler(logging.FileHandler(LOG_DIR / "litellm_debug.log"))

# %%
# Synthetic transcript with unambiguous facts (same as tests/test_extract.py).
transcript = (
    "I'm Alex, 38, male. Diagnosed with Crohn's four years ago. After mesalamine and "
    "prednisone failed, my gastroenterologist started me on Humira, which I've taken ever "
    "since and it keeps me in remission."
)

# out_dir=TESTS_OUT keeps this synthetic prediction in data/out/tests, not production.
labels = extract(transcript, "P000", out_dir=TESTS_OUT)
print(labels.model_dump_json(indent=2))
