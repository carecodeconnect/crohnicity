"""Dagster orchestration — the day-of entry point that runs the whole pipeline end-to-end and
shows which stage failed in the UI.

    uv run dg dev -m pipeline -d src     # UI at http://127.0.0.1:3000, then "Materialize all"

Data flow: ``interviews -> predictions -> {readme, referral_graphs}``; ``docsite`` is independent
(it documents the *source* docstrings, not the data). Extraction is **chunked** (``CHUNK_SIZE``
transcripts/call) to fit the Gemini free-tier ~20-requests/day cap. The model comes from ``config``
(``CROHNICITY_MODEL`` env var overrides ``config.json``). Input is the static committed
``data/in/interviews.json``, so there is **no sensor** — materialise on demand.

**Local-only — never commits to git.** The assets only write artefacts to disk (predictions,
README, graphs, docsite); publishing the updated artefacts to GitHub is a *separate, manual build
step* the human runs, not part of the orchestration.

**Instance home.** Dagster reads its config from ``$DAGSTER_HOME/dagster.yaml`` — the canonical
location, NOT the repo root (source of truth: https://docs.dagster.io/deployment/oss/dagster-yaml).
So ``DAGSTER_HOME`` points at a dedicated git-ignored ``.dagster_home/`` (set it in ``.env`` so the
command needs no prefix): ``.dagster_home/dagster.yaml`` is committed (config), its sqlite
run-storage is git-ignored (regenerated state), and it routes the readable run log to
``logs/dagster.log`` alongside the .py-script loguru logs.
"""

import subprocess
import sys
from pathlib import Path

import dagster as dg
from loguru import logger

# Dagster's `-f` loader doesn't add src/ to sys.path, so make the sibling modules importable here
# (mirrors pytest's `pythonpath=[src]` and the README.qmd setup chunk).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import referral_pathway_analysis as rpa  # noqa: E402
from config import CHUNK_SIZE, JSON_DIR, LOG_DIR, MODEL, ROOT  # noqa: E402
from main import load_interviews, run_chunked  # noqa: E402
from schema import Interview, PatientLabels  # noqa: E402

# Combined dg-run log: the in-process assets (extract, referral) log via loguru, so an unfiltered
# loguru sink here captures the whole run in one file. (Dagster's yaml python_logs only sees the
# stdlib `logging` module, not loguru — hence it stayed empty; see docs/DEV_SETUP.md.)
logger.add(LOG_DIR / "dagster.log", level="INFO", rotation="1 MB")


@dg.asset
def interviews() -> list[Interview]:
    """Load + validate data/in/interviews.json (the static committed input)."""
    return load_interviews()


@dg.asset
def predictions(interviews: list[Interview]) -> list[PatientLabels]:
    """Chunked extraction (CHUNK_SIZE/call) -> data/out/P*.json. A failed chunk surfaces here."""
    return run_chunked(interviews, MODEL, JSON_DIR, CHUNK_SIZE)


@dg.asset(deps=[predictions])
def referral_graphs() -> None:
    """Per-case journey graphs -> data/out/referral_pathway_*.html (reads the predictions)."""
    rpa.main()


@dg.asset(deps=[predictions])
def readme() -> None:
    """Post-extraction EDA report: quarto render -> README.md/html + plots (reads data/out)."""
    subprocess.run(
        ["uv", "run", "quarto", "render", "README.qmd"], cwd=ROOT, check=True
    )


@dg.asset
def docsite() -> None:
    """mkdocstrings API docsite -> site/. Independent: documents source docstrings, not the data."""
    subprocess.run(["uv", "run", "mkdocs", "build"], cwd=ROOT, check=True)


defs = dg.Definitions(
    assets=[interviews, predictions, referral_graphs, readme, docsite]
)
