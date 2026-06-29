"""Pipeline coordinator: chunked extraction over interviews.json via the fire CLI.

schema.py defines the shapes, extract.py makes the LLM call + persists each prediction; this module
slices the inputs and batches them. By default it runs **all 50 in chunks of 10 (5 calls)** — sized
to the free-tier 20-requests/day cap. Flags tune the slice/model for incremental or test runs:

    uv run python src/main.py                                          # all 50, chunks of 10 (5 calls)
    uv run python src/main.py --limit=10                              # run 1 only: P001-P010
    uv run python src/main.py --limit=10 --offset=10                  # run 2: P011-P020 (no re-run)
    uv run python src/main.py --model=ollama_chat/qwen3:30b-a3b --limit=1 --out-dir=data/out/tests
"""

import json
import sys
from pathlib import Path

import fire
import litellm
from loguru import logger
from pydantic import ValidationError

from config import CHUNK_SIZE, INTERVIEWS, JSON_DIR, MODEL
from extract import HANDLED, extract_batch, give_up_reason
from schema import Interview, PatientLabels

IN_PATH = INTERVIEWS  # committed input transcripts (config.INTERVIEWS)
RATE_LIMIT_DOCS = "https://ai.google.dev/gemini-api/docs/rate-limits"


def load_interviews(path: Path = IN_PATH) -> list[Interview]:
    """Load + validate interviews.json into a list of Interview records."""
    return [Interview.model_validate(r) for r in json.loads(path.read_text())]


def run_chunked(
    records: list[Interview], model: str, out_dir: Path, chunk_size: int
) -> list[PatientLabels]:
    """Run extract_batch over chunks of `chunk_size` — fewer Gemini requests for the daily cap.

    A chunk whose output is invalid/truncated (`JSONSchemaValidationError` / Pydantic
    `ValidationError`) is logged and **skipped** so one bad chunk can't abort the whole run; the
    skipped patients are counted + logged. Quota/overload errors (429/503) still propagate to stop
    the run, since continuing is futile (see `give_up_reason`)."""
    out: list[PatientLabels] = []
    skipped: list[str] = []
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        try:
            out += extract_batch(chunk, out_dir, model)
        except litellm.JSONSchemaValidationError, ValidationError:
            ids = [r.patient_id for r in chunk]
            skipped += ids
            logger.error(
                "chunk {} skipped (invalid/truncated output) — continuing run", ids
            )
    if skipped:
        logger.warning(
            "run_chunked: {}/{} patients skipped after extraction failures: {}",
            len(skipped),
            len(records),
            skipped,
        )
    return out


def main(
    model: str = MODEL,
    limit: int | None = None,
    offset: int = 0,
    chunk_size: int = CHUNK_SIZE,
    out_dir: str = str(JSON_DIR),
) -> str:
    """CLI (fire): extract interviews `[offset : offset+limit]` with `model`, `chunk_size`
    transcripts per call, into `out_dir`.

    **Default (bare command): all 50 transcripts in chunks of 10 → 5 API calls.** Sized to the
    Google AI (Gemini) **free tier's ~20 requests/day** cap, which we take as a fixed constraint:
    50 one-at-a-time calls would blow it, so we batch. `--limit`/`--offset` run a slice
    incrementally (e.g. one chunk per day, or to retry a failed chunk) without redoing earlier ones.
    """
    end = offset + limit if limit is not None else None
    records = load_interviews()[offset:end]
    try:
        results = run_chunked(records, model, Path(out_dir), chunk_size)
    except HANDLED as e:
        # The stop-vs-retry decision is encoded in give_up_reason(), not left to manual log-watching.
        if isinstance(e, litellm.RateLimitError):
            sys.exit(f"'{model}': {give_up_reason(e)} (see {RATE_LIMIT_DOCS})")
        sys.exit(f"'{model}': {give_up_reason(e)}")
    span = f"{records[0].patient_id}..{records[-1].patient_id}" if records else "—"
    return f"extracted {len(results)}/{len(records)} ({span}) -> {out_dir}"


if __name__ == "__main__":
    fire.Fire(main)
