# Notes on Dev Setup

I checked the following docs for installation steps.

I'd not used LiteLLM before, so I checked the docs:

- [LiteLLM setup](https://docs.litellm.ai/docs/#installation)

`requirements.txt` was requested, and uv uses `pyproject.toml`, so I needed to check how `uv` exports `requirements.txt`.

NB: The `requirements.txt` output looks a bit weird, with hash values, so might need to fix this if CAIO's build fails.

- [uv](https://docs.astral.sh/uv/concepts/projects/export/)

I had to Google the --private parameter for `gh`

- [gh](https://cli.github.com/manual/gh_repo_create)

I got an API key for Google API Studio:

- [Google AI Studio](https://aistudio.google.com/apikey)

I followed the instructions to export the API key as an environment variable here:

- [Using Gemini API Keys](https://ai.google.dev/gemini-api/docs/api-key#macos---zsh)

I added `config.env` to my `.gitignore` to protect the secret key, stopping it being added to git version control.

Then I got Google GenAI Python SDK working to test my API key works before trying `LiteLLM`, following this doc:

- [Gemini API Quickstart](https://ai.google.dev/gemini-api/docs/quickstart?_gl=1*1spt4le*_up*MQ..*_ga*MjAyMjcxMjk5MC4xNzgxNzA2ODEy*_ga_P1DBVKWT6V*czE3ODE3MDY4MTEkbzEkZzAkdDE3ODE3MDY4MTEkajYwJGwwJGgxMzYxOTQ0ODQy)

The toolchain rationale (uv for env/dependency management; ruff / ty / pytest as the Rust-coded
gate) is in **[CLAUDE.md → Stack](../CLAUDE.md#stack)** and **[Code style](../CLAUDE.md#code-style)** —
not restated here.

## First-time setup (one-off)

The uv / kernel / requirements-export commands are the canonical set in
**[CLAUDE.md → Commands](../CLAUDE.md#commands)** (`uv sync`,
`uv export … requirements.txt`, `ipykernel install`). The steps below are the ones *unique* to
standing up this repo:

```bash
# create a private GitHub repo using the gh cli tool
gh repo create crohnicity --private
# create environment variable
export GEMINI_API_KEY=<YOUR_API_KEY_HERE>
# source shell
source ~/.zshrc
# set upstream remote origin
git remote add origin https://github.com/carecodeconnect/crohnicity
# make initial commit
git add .
git commit -m "Initial commit"
git push --set-upstream origin main
# for the graphviz-rendered referral_pathway diagrams
brew install graphviz
```

**Rate limits & a local model.** The Gemini free-tier daily cap and the local-Ollama `--model`
swap (with litellm's `drop_params`) are documented in
**[SOLUTION → Usage](SOLUTION.qmd)** (the chunking strategy and the `--model` flag table); see
[`config.json`](../config.json) for the actual limits/ports. Reference docs:
[Gemini limits & tiers](https://ai.google.dev/gemini-api/docs/rate-limits) ·
[current usage](https://ai.dev/rate-limit) · [litellm Ollama](https://docs.litellm.ai/docs/providers/ollama).

## Running the pipeline (Dagster)

How to launch a run (UI *Materialize all* vs. headless `dg launch`), the asset graph, and the
free-tier chunking are in **[SOLUTION → Usage](SOLUTION.qmd)**; ports come from
[`config.json`](../config.json) (`dagster_port`). The Dagster-setup details *unique* to this doc:

**`DAGSTER_HOME` in `.env`.** Dagster keeps run history in a temp dir by default (wiped on exit).
To persist it, point `DAGSTER_HOME` at the dedicated, git-ignored `.dagster_home/` instance home —
add this **machine-specific** line to your `.env` (like `GEMINI_API_KEY`), so the `dg` commands
need no env-var prefix:

```bash
DAGSTER_HOME=/absolute/path/to/crohnicity/.dagster_home
```

Inside `.dagster_home/`, **`dagster.yaml` is committed** (it's config, not a secret — it shows how
the instance is wired: telemetry off) while the regenerated sqlite run-storage is git-ignored.

**The run log is a loguru sink, not `dagster.yaml`.** The flat `logs/dagster.log` run log is
written by a **loguru sink in `src/pipeline.py`**, *not* by `dagster.yaml`: our app logs through
**loguru**, but Dagster's yaml `python_logs` handler only captures the stdlib `logging` module — so
a yaml-defined sink stayed empty. The in-process assets (`predictions`, `referral_graphs`) already
log via loguru, so an unfiltered loguru sink in `pipeline.py` captures the whole materialization in
one file, alongside the per-script logs.

**`dg` project layer.** The `dg` CLI is a *project layer* over our setup: `[tool.dg]` in
`pyproject.toml` (`directory_type = "project"` + `[tool.dg.project] code_location_target_module`)
tells `dg` where the `Definitions` live — **separate** from the *instance* config (`dagster.yaml`
in `$DAGSTER_HOME`). Because our modules live in `src/` (not an installed package), `dg` takes
`-m pipeline -d src` (`-m` loads the module, `--working-directory src` lets it import) — run it from
the **repo root** so `.env` (`DAGSTER_HOME`, `GEMINI_API_KEY`) still loads. Config schema:
[dg-cli-configuration](https://docs.dagster.io/api/clis/dg-cli/dg-cli-configuration). We use a plain
`Definitions` object (via `code_location_target_module`), **not** the Components `defs/` folder
layout — so `dg dev` / `dg launch` / `dg list defs` are the commands; `dg check defs` is
Components-only and N/A here. As a composable CLI, `dg` suits coding-agent / CI workflows: an agent
can run `dg list defs` / `dg check` / `dg launch` and parse the output to validate project-level
dependencies and code-location structure *before* a run — version-controllable, not UI-bound, since
the project config is committed in `pyproject.toml`.

### Relocating / renaming the project root

Renaming the project folder (e.g. `chronicity` → `crohnicity`) breaks the venv's and kernel's
absolute paths, so after renaming + reopening the editor:

```bash
uv sync --reinstall                                                       # recreate .venv AND rewrite console-script shebangs (pytest, etc.) for the new path — not plain `uv sync`
uv run python -m ipykernel install --user --name crohnicity --display-name "Python (crohnicity)"   # re-point the jupyter kernel (used by the notebooks + docs/SOLUTION.qmd)
git remote set-url origin https://github.com/carecodeconnect/crohnicity.git
uv run quarto render docs/SOLUTION.qmd                                     # regenerate docs/SOLUTION.md (gfm)
uv run python src/referral_pathway_analysis.py                            # regenerate the per-case graphs
RUN_RENDER_TEST=1 uv run pytest tests/test_render.py                      # verify the render pipeline end-to-end
```

**Why `--reinstall` and not plain `uv sync`:** a rename leaves the venv's Python console-scripts
(`.venv/bin/pytest`, …) with a shebang hardcoding the *old* interpreter path, so `uv run pytest`
fails with `Failed to spawn: pytest — No such file or directory (os error 2)`. Plain `uv sync` sees
the packages already installed and won't regenerate the scripts; `--reinstall` forces the
entry-point shebangs to be rewritten to the new path. Native binaries (`ruff`, `ty`) have no shebang
and keep working — which is why *only* `pytest` breaks after a rename. (If `--reinstall` ever isn't
enough, `rm -rf .venv && uv sync` recreates the venv from scratch.)

## Code review — the in-editor diff workflow

I run Claude Code in VS Code's integrated terminal in **"Explanatory"** output style (committed as
`"outputStyle": "Explanatory"` in `.claude/settings.json`). **Every single change** CC makes
surfaces as a **diff in a VS Code window**, and I review that diff before accepting it — so every
update is checked against my intent before it lands, kept **small and self-contained per commit**.
The Explanatory "Insights" explain *why* each change was made, making the diff review faster.

To reproduce so edits show as diffs in the **editor panes** (not just the terminal):

1. **VS Code ≥ 1.98** with the official **Claude Code** extension — publisher **Anthropic**, id
   [`anthropic.claude-code`](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)
   (Extensions view → search "Claude Code" → Install).
2. Install the **standalone CLI** so `claude` is on `PATH` — the extension bundles its own CLI for
   the chat panel but does **not** add `claude` to the terminal.
3. Run **`claude` in VS Code's integrated terminal** (`` Ctrl+` `` / `` Cmd+` ``); it auto-connects
   to the IDE. From an external terminal, run **`/ide`** to connect.

No "diff tool" setting is involved: an active extension runs a local **`ide` MCP server**, and the
connected CLI uses it to open every edit in VS Code's native diff viewer.

I also set the [output mode](https://code.claude.com/docs/en/output-styles) via `/config` and
exported my CC chat history with `/export` to record the prompting strategies. The one-off `.py`
transformation scripts CC produced (the ground-truth spreadsheet builders) are kept in `sandbox/`
as a record of the diffs I reviewed.

## Notebooks — jupytext pairing

CLAUDE.md names this doc as the canonical jupytext workflow. The rule (edit the `.py`, never
hand-edit the `.ipynb`, `jupytext --sync`) is summarised in
[CLAUDE.md → Architecture notes](../CLAUDE.md#architecture-notes); the operational detail lives here.

`.ipynb` JSON doesn't diff cleanly, so each notebook is **paired with a `py:percent` script via
[jupytext](https://jupytext.readthedocs.io)**: the `.py` holds *code* (the editing source of truth)
and the `.ipynb` holds *code + outputs* (the running / viewing copy). They don't conflict —
`jupytext --sync` propagates code edits into the `.ipynb` while **preserving its outputs**, and
*running* the notebook changes only outputs. Rule of thumb: after editing a `.py`, sync before
running.

```bash
# after editing the .py, propagate to the .ipynb (outputs preserved):
jupytext --sync notebooks/03_extraction_test.py

# after editing or running the .ipynb, propagate code back to the .py:
jupytext --sync notebooks/03_extraction_test.ipynb

# pair a brand-new notebook once (creates the .py and links the two):
jupytext --set-formats ipynb,py:percent notebooks/<name>.ipynb
```

`jupytext --sync` uses the more-recently-edited side as the source, so passing either file works.
If *both* sides changed since the last sync it refuses — force a direction with
`jupytext --to ipynb --update notebooks/<name>.py` (keeps the `.ipynb` outputs).

`notebooks/` is **excluded from the quality gate** (ruff / ty / pytest are scoped to `src`/`tests` —
see `tests/type_lint_unit_tests.sh` and `pyproject.toml`): these scripts are prototyping mirrors,
not shipped code.
