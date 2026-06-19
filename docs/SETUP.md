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

The one-off `.py` transformation scripts CC produced (the ground-truth spreadsheet builders)
are kept in `sandbox/` as a record of the diffs I reviewed.