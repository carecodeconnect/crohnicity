#!/usr/bin/env bash
# Manual quality gate (in lieu of pre-commit) — run on each major code update:
#   bash tests/type_lint_unit_tests.sh
set -u
fail=0
uv run ruff check src tests          || fail=1
uv run ruff format --check src tests || fail=1
uv run ty check                      || fail=1
uv run pytest -q                     || fail=1
exit "$fail"
