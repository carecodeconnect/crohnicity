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
- **Rate limits** — the free tier caps Gemini 2.5 Flash Lite at **~20 requests/day** (under the 50
  transcripts, so a full run needs a paid tier or spreading across days):
  [limits & tiers](https://ai.google.dev/gemini-api/docs/rate-limits) ·
  [current usage](https://ai.dev/rate-limit)
- **Local model (Ollama)** to dodge the quota — `uv run python src/main.py --model=ollama_chat/<model>`
  (needs `ollama serve` running and `ollama pull <model>`; the same call works via litellm's
  `drop_params`, which drops the Gemini-only `response_schema`/`enforce_validation`).
  Docs: [litellm Ollama](https://docs.litellm.ai/docs/providers/ollama)

I added `config.env` to my `.gitignore` to protect the secret key, stopping it being added to git version control.

Then I got Google GenAI Python SDK working to test my API key works before trying `LiteLLM`, following this doc:

- [Gemini API Quickstart](https://ai.google.dev/gemini-api/docs/quickstart?_gl=1*1spt4le*_up*MQ..*_ga*MjAyMjcxMjk5MC4xNzgxNzA2ODEy*_ga_P1DBVKWT6V*czE3ODE3MDY4MTEkbzEkZzAkdDE3ODE3MDY4MTEkajYwJGwwJGgxMzYxOTQ0ODQy)


I enjoy using `uv` for Python environment/dependency management and wanted to try Ruff for linting (instead of Black) and Py for type checking, to complete my fast Rust-coded dev tool chain along with using `pytest` for unit testing as requested.

- [uv](https://docs.astral.sh/uv/)

- [ruff](https://astral.sh/ruff)

- [ty](https://docs.astral.sh/ty/)

- [pytest](https://docs.pytest.org/en/stable/)

```python
# initialise the uv venv
uv sync
# recreate requirements.txt
uv export --format requirements.txt --output-file requirements.txt 
# sync uv venv with jupyter kernel called "crohnicity" so i can recognise it in my juypyter notebook
uv run python -m ipykernel install --user --name "$(basename $PWD)" --display-name "Python ($(basename $PWD))"
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
# for experimenting with graphviz non-linear cyclical referral_pathway diagram
brew install graphviz
```

## Running the pipeline (Dagster)

`src/pipeline.py` is the Dagster orchestration (assets `interviews -> predictions -> {readme,
referral_graphs}`, plus an independent `docsite`). `dagster dev` needs the **`dagster-webserver`**
package installed alongside `dagster` (already a dependency). There are **two ways to launch a run**,
for different situations:

**1. From the UI — canonical for `dagster dev` (interactive dev loop).** The dev server *is* the
launcher: start it, then materialise from the browser. In the UI: **Assets** tab → **"Materialize
all"** (or select `predictions` / `readme` / … → Materialize). The server stays running in its
terminal; you click in the browser.

```bash
uv run dg dev -m pipeline -d src     # http://127.0.0.1:3000 -> "Materialize all"
```

**2. Headless from a second terminal (CLI) — scripted / CI, no UI.** Runs in its own process:

```bash
uv run dg launch --assets "*" -m pipeline -d src
```

(`-f` scopes to that one file; `-m` / `--package-name` would load a whole module / package.)
Materialising **all** runs the full pipeline: 50-transcript inference (chunked 10×5 to fit the
free-tier cap) → EDA / README render → referral graphs → docsite, with per-stage failure visibility.

**dg project config.** The `dg` CLI is a *project layer* over our setup: `[tool.dg]` in
`pyproject.toml` (`directory_type = "project"` + `[tool.dg.project] code_location_target_module =
"pipeline"`) tells `dg` where the `Definitions` live — **separate** from the *instance* config
(`dagster.yaml` in `$DAGSTER_HOME`). Because our modules live in `src/` (not an installed package),
`dg` takes **`-m pipeline -d src`** (`-m` loads the module, `--working-directory src` lets it import) — run it from the **repo
root** so `.env` (`DAGSTER_HOME`, `GEMINI_API_KEY`) still loads. Config schema:
[dg-cli-configuration](https://docs.dagster.io/api/clis/dg-cli/dg-cli-configuration). We use a plain
`Definitions` object (via `code_location_target_module`), **not** the Components `defs/` folder
layout — so `dg dev` / `dg launch` / `dg list defs` are the commands; `dg check defs` is
Components-only and N/A here.

**Why `dg` suits agentic / CLI workflows.** As a composable CLI, `dg` fits coding-agent workflows
(e.g. Claude Code) well: an agent can run `dg list defs` / `dg check` / `dg launch` and parse the
output to validate project-level dependencies, paths and code-location structure *before* a run —
version-controllable and reproducible, not UI-bound. The project config is committed in
`pyproject.toml`, so the same checks run identically in an agent session or in CI.

**Run vs. asset materialization.** Hierarchical, not alternatives: **materializing an asset**
executes its function and persists the result (an *AssetMaterialization* event) — the asset-centric
"produce/refresh this object"; a **run** is the *execution container* (its own run ID, status, logs,
"Runs" tab). A materialization always happens *inside* a run, so clicking **"Materialize all"**
launches one run that materializes the selected assets (`interviews -> predictions -> {readme,
referral_graphs}` + `docsite`). Sources: [Assets](https://docs.dagster.io/guides/build/assets),
[execution API](https://docs.dagster.io/api/dagster/execution).

**Configuration feeding a run.** Two kinds: **`.env`** (secrets — `GEMINI_API_KEY`; Dagster
auto-loads it and logs the line you see) and **`config.json`** (model, paths, chunk size; loaded
*silently* by `src/config.py` when Dagster imports the code, then used during materialization — no
log line because it's our plain `json.loads`, not a Dagster mechanism). Dagster keeps run history in
a temp dir by default (wiped on exit). To persist it, set **`DAGSTER_HOME`** to the dedicated,
git-ignored **`.dagster_home/`** instance home — add this line to your `.env` (machine-specific,
like `GEMINI_API_KEY`), so the commands above need no env-var prefix:

```bash
DAGSTER_HOME=/absolute/path/to/crohnicity/.dagster_home
```

Inside `.dagster_home/`, **`dagster.yaml` is committed** (it's config, not a secret — it shows how
the instance is wired: telemetry off) while the regenerated sqlite run-storage is git-ignored. The
flat **`logs/dagster.log`** run log is written by a **loguru sink in `src/pipeline.py`**, *not* by
`dagster.yaml`: our app logs through **loguru**, but Dagster's yaml `python_logs` handler only
captures the stdlib `logging` module — so a yaml-defined sink stayed empty. The in-process assets
(`predictions`, `referral_graphs`) already log via loguru, so an unfiltered loguru sink in
`pipeline.py` captures the whole materialization in one file, alongside the per-script logs.
**Dagster runs locally only** — it never pushes to GitHub; publishing the refreshed artefacts
(data + logs + README) is a separate, manual `git` step.

### Relocating / renaming the project root

Renaming the project folder (e.g. `chronicity` → `crohnicity`) breaks the venv's and kernel's
absolute paths, so after renaming + reopening the editor:

```bash
uv sync --reinstall                                                       # recreate .venv AND rewrite console-script shebangs (pytest, etc.) for the new path — not plain `uv sync`
uv run python -m ipykernel install --user --name crohnicity --display-name "Python (crohnicity)"   # re-point the jupyter kernel (used by the notebooks + README.qmd)
git remote set-url origin https://github.com/carecodeconnect/crohnicity.git
uv run quarto render README.qmd                                           # regenerate README.md (gfm)
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

- When using Claude Code, I set the [output mode](https://code.claude.com/docs/en/output-styles) to "Explanatory" mode using `/config`. This mode "Provides educational “Insights” in between helping you complete software engineering tasks. Helps you understand implementation choices and codebase patterns." Rather than CC writing the code, I copied out the code snippets by hand, so I could understand the implications of each step. 

- I exported my CC chat history using the `/export` command to show the prompting strategies I used in Explanatory mode.

## Code review

I run Claude Code in an integrated terminal inside VS Code, in "Explanatory" output style (set
in `.claude/settings.json`). **Every single change** CC makes surfaces as a **diff in a VS Code
window**, and I review that diff before accepting it — so every update is checked against my
intent before it lands. The Explanatory "Insights" explain *why* each change was made, which
makes the diff review faster and more deliberate. Changes are kept **small and self-contained
per commit** — minimal, concise edits, not giant PR-style batches — so each commit reads as a
diff I can review easily.

### Reproducing the in-editor diff workflow

So edits show as diffs in the **editor panes** (not just the terminal):

1. **VS Code ≥ 1.98** with the official **Claude Code** extension — publisher **Anthropic**, id
   [`anthropic.claude-code`](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code)
   (Extensions view → search "Claude Code" → Install).
2. Install the **standalone CLI** so `claude` is on `PATH` — the extension bundles its own CLI for
   the chat panel but does **not** add `claude` to the terminal.
3. Run **`claude` in VS Code's integrated terminal** (`` Ctrl+` `` / `` Cmd+` ``); it auto-connects
   to the IDE. From an external terminal, run **`/ide`** to connect.

No "diff tool" setting is involved: an active extension runs a local **`ide` MCP server**, and the
connected CLI uses it to open every edit in VS Code's native diff viewer. The only committed repo
setting is `"outputStyle": "Explanatory"` in `.claude/settings.json`.

The one-off `.py` transformation scripts CC produced (the ground-truth spreadsheet builders)
are kept in `sandbox/` as a record of the diffs I reviewed.

## Notebooks — jupytext pairing

`.ipynb` JSON doesn't diff cleanly in VS Code, so each notebook is **paired with a `py:percent`
script via [jupytext](https://jupytext.readthedocs.io)**. The pair splits responsibilities:

- **The `.py` is the *editing* source of truth** — Claude Code makes notebook code changes here,
  so they land as clean, reviewable diffs.
- **The `.ipynb` is the *running / viewing* source of truth** — you execute and read it in VS Code
  / Jupyter, and its cell **outputs live here** (the `.py` stores code only).

These don't conflict, because `py:percent` holds *code* and `.ipynb` holds *code + outputs*:
`jupytext --sync` propagates code edits from the `.py` into the `.ipynb` while **preserving its
outputs**, and *running* the notebook changes only outputs — never the code. Rule of thumb: after
editing a `.py`, sync before running; don't hand-edit the same code in both at once.

```bash
# Claude's side — after editing the .py, propagate to the .ipynb (outputs preserved):
jupytext --sync notebooks/03_extraction_test.py

# Your side — after editing or running the .ipynb, propagate code back to the .py:
jupytext --sync notebooks/03_extraction_test.ipynb

# Pair a brand-new notebook once (creates the .py and links the two):
jupytext --set-formats ipynb,py:percent notebooks/<name>.ipynb
```

`jupytext --sync` uses the more-recently-edited side as the source, so passing either file works.
If *both* sides changed since the last sync it refuses (the "don't hand-edit both" rule) — force a
direction with `jupytext --to ipynb --update notebooks/<name>.py` (keeps the `.ipynb` outputs).

`notebooks/` is **excluded from the quality gate** — ruff, ty, and pytest are scoped to
`src`/`tests` (see `tests/type_lint_unit_tests.sh` and `pyproject.toml`). These scripts are
prototyping mirrors, not shipped code, so they aren't linted, type-checked, or collected as tests.