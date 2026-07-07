"""Central config — the single source of truth for paths and parameters, loaded from
``config.json`` at the repo root.

Every script (the ``src/`` modules and the ``docs/SOLUTION.qmd`` chunks) imports these constants instead
of hard-coding the model name or a path, so swapping the model or bumping the gold-set version is a
one-line edit in ``config.json``. Paths resolve against the repo root, so they hold regardless of
the caller's working directory.
"""

import json
import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_CFG = json.loads((ROOT / "config.json").read_text())
# App version — single source of truth is pyproject.toml [project] version.
APP_VERSION: str = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
    "version"
]

# Model default from config.json; the CROHNICITY_MODEL env var overrides it (e.g. a local Ollama
# model, ollama_chat/qwen3:8b), and main.py's --model flag overrides per-invocation.
MODEL: str = os.getenv("CROHNICITY_MODEL", _CFG["model"])
TEMPERATURE: float = _CFG[
    "temperature"
]  # 0 = greedy/deterministic (extraction is classification)
INTERVIEWS = ROOT / _CFG["interviews"]  # committed source transcripts
GOLD = ROOT / _CFG["gold"]  # hand-annotated gold set (versioned .ods) for the eval
PROMPT = ROOT / _CFG["prompt"]  # system prompt, kept as its own reviewable artifact
OUT_DIR = ROOT / _CFG["out_dir"]  # base output dir (holds json/, html/, plots/, tests/)
JSON_DIR = ROOT / _CFG["json_dir"]  # per-patient prediction JSON
HTML_DIR = ROOT / _CFG["html_dir"]  # per-case referral_pathway graphs
PLOTS_DIR = ROOT / _CFG["plots_dir"]  # EDA plots embedded in docs/SOLUTION.md
LOG_DIR = ROOT / _CFG["log_dir"]  # loguru sinks
DAGSTER_PORT: int = _CFG[
    "dagster_port"
]  # Dagster dev UI port (passed to `dg dev -p`; see DEV_SETUP)
DOCSITE_PORT: int = _CFG[
    "docsite_port"
]  # MkDocs preview port (passed to `mkdocs serve -a`; see DEV_SETUP)
API_PORT: int = _CFG[
    "api_port"
]  # FastAPI service port (app/main.py; EXPOSEd by the Dockerfile)
CHUNK_SIZE: int = _CFG[
    "chunk_size"
]  # transcripts per Gemini call (free-tier RPD workaround)
# Quota-aware retry: litellm's own retries are OFF (a failed free-tier request costs the same daily
# quota as a successful one). We retry ONLY 503 (transient overload), sparingly; never 429.
RETRY_503_MAX: int = _CFG["retry_503_max"]  # extra retries on a 503 ServiceUnavailable
RETRY_503_DELAY_S: int = _CFG[
    "retry_503_delay_s"
]  # seconds to wait between 503 retries
MAX_TOKENS: int = _CFG["max_tokens"]  # batch-call completion headroom
