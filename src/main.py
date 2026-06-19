"""Pipeline coordinator: loop the single-call extract.extract() over interviews.json.

Thin orchestration — schema.py defines the shapes, extract.py makes one LLM call + persists it,
and this module loads the inputs and runs extract over each patient. CLI via python-fire:

    uv run python src/main.py --limit=3
    uv run python src/main.py --model=gemini/gemini-2.5-flash
    uv run python src/main.py --model=ollama_chat/gemma4   # local; needs `ollama serve`
"""

import json
import sys
from pathlib import Path

import fire
import litellm

from extract import HANDLED, MODEL, OUT_DIR, ROOT, extract
from schema import Interview, PatientLabels

IN_PATH = ROOT / "data" / "in" / "interviews.json"  # committed input transcripts
RATE_LIMIT_DOCS = "https://ai.google.dev/gemini-api/docs/rate-limits"


def load_interviews(path: Path = IN_PATH) -> list[Interview]:
    """Load + validate interviews.json into a list of Interview records."""
    return [Interview.model_validate(r) for r in json.loads(path.read_text())]


def run(
    records: list[Interview], model: str = MODEL, out_dir: Path = OUT_DIR
) -> list[PatientLabels]:
    """Run extract() over each interview with `model` -> list[PatientLabels] (each persisted)."""
    return [
        extract(r.interview_transcript, r.patient_id, out_dir, model) for r in records
    ]


def main(model: str = MODEL, limit: int | None = None) -> str:
    """CLI (fire): extract the first `limit` interviews (or all) with `model`."""
    records = load_interviews()[:limit]
    try:
        results = run(records, model=model)
    except HANDLED as e:
        if isinstance(e, litellm.RateLimitError):
            sys.exit(f"Rate limit / quota hit for '{model}' — see {RATE_LIMIT_DOCS}")
        if isinstance(e, litellm.APIConnectionError):
            sys.exit(f"Could not reach '{model}' — check the name / `ollama serve`.")
        if isinstance(e, litellm.JSONSchemaValidationError):
            sys.exit(f"'{model}' didn't match the schema — try a more capable model.")
        sys.exit(f"'{model}' failed: {type(e).__name__} — see logs/.")
    return f"extracted {len(results)}/{len(records)} -> {OUT_DIR}"


if __name__ == "__main__":
    fire.Fire(main)
