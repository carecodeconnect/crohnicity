"""Central config — the single source of truth for paths and parameters, loaded from
``config.json`` at the repo root.

Every script (the ``src/`` modules and the ``README.qmd`` chunks) imports these constants instead
of hard-coding the model name or a path, so swapping the model or bumping the gold-set version is a
one-line edit in ``config.json``. Paths resolve against the repo root, so they hold regardless of
the caller's working directory.
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_CFG = json.loads((ROOT / "config.json").read_text())

# Model default from config.json; the CROHNICITY_MODEL env var overrides it (e.g. a local Ollama
# model, ollama_chat/qwen3:8b), and main.py's --model flag overrides per-invocation.
MODEL: str = os.getenv("CROHNICITY_MODEL", _CFG["model"])
INTERVIEWS = ROOT / _CFG["interviews"]  # committed source transcripts
GOLD = ROOT / _CFG["gold"]  # hand-annotated gold set (versioned .ods) for the eval
PROMPT = ROOT / _CFG["prompt"]  # system prompt, kept as its own reviewable artifact
OUT_DIR = ROOT / _CFG["out_dir"]  # persisted predictions
PLOTS_DIR = ROOT / _CFG["plots_dir"]  # EDA plots embedded in the README
LOG_DIR = ROOT / _CFG["log_dir"]  # loguru sinks
CHUNK_SIZE: int = _CFG[
    "chunk_size"
]  # transcripts per Gemini call (free-tier RPD workaround)
MAX_RETRIES: int = _CFG["max_retries"]  # litellm retries transient 429/503 with backoff
MAX_TOKENS: int = _CFG["max_tokens"]  # batch-call completion headroom
