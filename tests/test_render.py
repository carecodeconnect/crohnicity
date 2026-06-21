"""Gated end-to-end smoke test for the post-extraction EDA render (RUN_RENDER_TEST=1).

Runs `quarto render README.qmd` and checks the GFM output is clean: no unresolved inline
`{python}` expressions (kernel/exec worked) and no leaked great_tables CSS. This exercises the
whole render path — the `crohnicity` jupyter kernel, quarto, and the EDA chunks reading data/out —
so it's the check to run after relocating/renaming the project (`uv sync` + re-register kernel).
Gated (needs quarto + the kernel + the venv), like the live/ollama tests.
"""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_readme_renders_clean() -> None:
    """`quarto render README.qmd` succeeds and produces drift-free, CSS-free GFM."""
    if os.getenv("RUN_RENDER_TEST") != "1":
        pytest.skip("RUN_RENDER_TEST != 1 — quarto render smoke test skipped")
    result = subprocess.run(
        ["uv", "run", "quarto", "render", "README.qmd"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    md = (ROOT / "README.md").read_text()
    assert "{python}" not in md, "unresolved inline code — kernel/exec failed"
    assert "<style>" not in md and "gt_table" not in md, (
        "great_tables CSS leaked into GFM"
    )
