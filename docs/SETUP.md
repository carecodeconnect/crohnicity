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
# sync uv venv with jupyter kernel called "chronicity" so i can recognise it in my juypyter notebook
uv run python -m ipykernel install --user --name "$(basename $PWD)" --display-name "Python ($(basename $PWD))"
# create a private GitHub repo using the gh cli tool
gh repo create chronicity --private 
# create environment variable
export GEMINI_API_KEY=<YOUR_API_KEY_HERE>
# source shell
source ~/.zshrc
# set upstream remote origin
git remote add origin https://github.com/carecodeconnect/chronicity
# make initial commit
git add .
git commit -m "Initial commit"
git push --set-upstream origin main
# for experimenting with graphviz non-linear cyclical referral_pathway diagram
brew install graphviz
```

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