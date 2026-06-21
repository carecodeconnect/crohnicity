# Crohnicity: Mama Health Challenge


<!-- Source of truth: edit README.qmd, then `uv run quarto render README.qmd` to regenerate
     README.md (gfm) + README.html (local verification). The analysis chunks read only the
     persisted predictions in data/out/ — no Gemini API calls. -->

## Pydantic Schema Design

- Which fields should be **enums** vs. **free text** vs. **structured
  objects** (e.g., a list of treatment records with name, class,
  outcome, reason_stopped)?
- How do you distinguish **“not mentioned”** from **“explicitly
  denied”** from **“cut off before we could find out”**? These are three
  very different states and they matter for the analysis.
- How do you capture **evidence** — a supporting snippet, turn
  reference, or rationale per extracted field — so a reviewer can audit
  the model’s decisions?
- Socio-demographic fields: what’s worth extracting, what’s noise?

## Extraction Pipeline

- **Single-shot vs. multi-stage extraction.** One big call, or a
  pipeline (e.g., identify-then-extract, or narrative-then-structured)?
  What are the tradeoffs?
- **Prompt design for uncertainty.** How do you instruct the model to
  separate absence, negation, and truncation?
- **Determinism and reproducibility.** Temperature, structured output
  mode, seed, caching — what did you pick and why?

## Evaluation

Pick **one** approach that gives you a real signal on quality. We don’t
need a rigorous eval harness — we want to see you know how to probe your
own pipeline:

1.  **Mini golden set:** hand-label 5–10 transcripts yourself on key
    fields, compute agreement with the model, **or**
2.  **LLM-as-judge:** a second LLM call scoring extraction fidelity on a
    sample against the source transcript, **or**
3.  **Consistency check:** run extraction twice (different prompts,
    temperatures, or models) and use disagreement as a proxy for
    reliability.

Write up what it told you in a few lines: what the pipeline is solid on,
where it’s shaky, what you’d fix first with more time.

I picked (1).

## Analysis

A short answer to PharmaCorp’s four questions. Numbers with ranges or
caveats where sensible. Keep it tight — the point is to demonstrate the
structured output is usable, not to write a consulting deck.

1.  What percentage of patients in the dataset appear to be on a
    biologic?
2.  For patients *not* on a biologic, what are the primary reasons
    (doctor choice, patient fears, cost, access, something else)?
3.  What other treatments are commonly tried or discussed before a
    biologic is considered?
4.  What does a typical referral pathway look like, in number of steps
    from GP to a specialist who can prescribe a biologic?

### Answers

Computed from the persisted predictions in `data/out/` (`n = 50`).

**Q1 — % on a biologic.**

<div id="xkqtiloaxd" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>
#xkqtiloaxd table {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', 'Fira Sans', 'Droid Sans', Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
&#10;#xkqtiloaxd thead, tbody, tfoot, tr, td, th { border-style: none; }
 tr { background-color: transparent; }
#xkqtiloaxd p { margin: 0; padding: 0; }
 #xkqtiloaxd .gt_table { display: table; border-collapse: collapse; line-height: normal; margin-left: auto; margin-right: auto; color: #333333; font-size: 16px; font-weight: normal; font-style: normal; background-color: #FFFFFF; width: auto; border-top-style: solid; border-top-width: 2px; border-top-color: #A8A8A8; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #A8A8A8; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; }
 #xkqtiloaxd .gt_caption { padding-top: 4px; padding-bottom: 4px; }
 #xkqtiloaxd .gt_title { color: #333333; font-size: 125%; font-weight: initial; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; border-bottom-color: #FFFFFF; border-bottom-width: 0; }
 #xkqtiloaxd .gt_subtitle { color: #333333; font-size: 85%; font-weight: initial; padding-top: 3px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; border-top-color: #FFFFFF; border-top-width: 0; }
 #xkqtiloaxd .gt_heading { background-color: #FFFFFF; text-align: center; border-bottom-color: #FFFFFF; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #xkqtiloaxd .gt_bottom_border { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #xkqtiloaxd .gt_col_headings { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #xkqtiloaxd .gt_col_heading { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; overflow-x: hidden; }
 #xkqtiloaxd .gt_column_spanner_outer { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; padding-top: 0; padding-bottom: 0; padding-left: 4px; padding-right: 4px; }
 #xkqtiloaxd .gt_column_spanner_outer:first-child { padding-left: 0; }
 #xkqtiloaxd .gt_column_spanner_outer:last-child { padding-right: 0; }
 #xkqtiloaxd .gt_column_spanner { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; overflow-x: hidden; display: inline-block; width: 100%; }
 #xkqtiloaxd .gt_spanner_row { border-bottom-style: hidden; }
 #xkqtiloaxd .gt_group_heading { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; text-align: left; }
 #xkqtiloaxd .gt_empty_group_heading { padding: 0.5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: middle; }
 #xkqtiloaxd .gt_from_md> :first-child { margin-top: 0; }
 #xkqtiloaxd .gt_from_md> :last-child { margin-bottom: 0; }
 #xkqtiloaxd .gt_row { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; margin: 10px; border-top-style: solid; border-top-width: 1px; border-top-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; overflow-x: hidden; }
 #xkqtiloaxd .gt_stub { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; }
 #xkqtiloaxd .gt_stub_row_group { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; vertical-align: top; }
 #xkqtiloaxd .gt_row_group_first td { border-top-width: 2px; }
 #xkqtiloaxd .gt_row_group_first th { border-top-width: 2px; }
 #xkqtiloaxd .gt_striped { color: #333333; background-color: #F4F4F4; }
 #xkqtiloaxd .gt_table_body { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #xkqtiloaxd .gt_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #xkqtiloaxd .gt_first_summary_row { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; }
 #xkqtiloaxd .gt_last_summary_row_top { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #xkqtiloaxd .gt_grand_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #xkqtiloaxd .gt_first_grand_summary_row_bottom { border-top-style: double; border-top-width: 6px; border-top-color: #D3D3D3; }
 #xkqtiloaxd .gt_last_grand_summary_row_top { border-bottom-style: double; border-bottom-width: 6px; border-bottom-color: #D3D3D3; }
 #xkqtiloaxd .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #xkqtiloaxd .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #xkqtiloaxd .gt_left { text-align: left; }
 #xkqtiloaxd .gt_center { text-align: center; }
 #xkqtiloaxd .gt_right { text-align: right; font-variant-numeric: tabular-nums; }
 #xkqtiloaxd .gt_font_normal { font-weight: normal; }
 #xkqtiloaxd .gt_font_bold { font-weight: bold; }
 #xkqtiloaxd .gt_font_italic { font-style: italic; }
 #xkqtiloaxd .gt_super { font-size: 65%; }
 #xkqtiloaxd .gt_footnotes { color: font-color(#FFFFFF); background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #xkqtiloaxd .gt_footnote { margin: 0px; font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; }
 #xkqtiloaxd .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #xkqtiloaxd .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #xkqtiloaxd .gt_footnote_marks { font-size: 75%; vertical-align: 0.4em; position: initial; }
 #xkqtiloaxd .gt_asterisk { font-size: 100%; vertical-align: 0; }
 &#10;</style>

| Q1 — patients on a biologic |          |      |
|-----------------------------|----------|------|
| status                      | patients | pct  |
| on a biologic (taken)       | 37       | 74.0 |
| not on a biologic           | 13       | 26.0 |

&#10;</div>

74% of patients (37/50) appear to be **on a biologic**
(`biologic_taken == true`).

*Evaluation — mini golden set.* `biologic_taken` (the field Q1 rests on)
scored against the hand-annotated gold in `_v5.ods` (the `to_review`
cases), as precision / recall / F1:

<div id="ihrxaykfke" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>
#ihrxaykfke table {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', 'Fira Sans', 'Droid Sans', Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
&#10;#ihrxaykfke thead, tbody, tfoot, tr, td, th { border-style: none; }
 tr { background-color: transparent; }
#ihrxaykfke p { margin: 0; padding: 0; }
 #ihrxaykfke .gt_table { display: table; border-collapse: collapse; line-height: normal; margin-left: auto; margin-right: auto; color: #333333; font-size: 16px; font-weight: normal; font-style: normal; background-color: #FFFFFF; width: auto; border-top-style: solid; border-top-width: 2px; border-top-color: #A8A8A8; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #A8A8A8; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; }
 #ihrxaykfke .gt_caption { padding-top: 4px; padding-bottom: 4px; }
 #ihrxaykfke .gt_title { color: #333333; font-size: 125%; font-weight: initial; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; border-bottom-color: #FFFFFF; border-bottom-width: 0; }
 #ihrxaykfke .gt_subtitle { color: #333333; font-size: 85%; font-weight: initial; padding-top: 3px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; border-top-color: #FFFFFF; border-top-width: 0; }
 #ihrxaykfke .gt_heading { background-color: #FFFFFF; text-align: center; border-bottom-color: #FFFFFF; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #ihrxaykfke .gt_bottom_border { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #ihrxaykfke .gt_col_headings { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #ihrxaykfke .gt_col_heading { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; overflow-x: hidden; }
 #ihrxaykfke .gt_column_spanner_outer { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; padding-top: 0; padding-bottom: 0; padding-left: 4px; padding-right: 4px; }
 #ihrxaykfke .gt_column_spanner_outer:first-child { padding-left: 0; }
 #ihrxaykfke .gt_column_spanner_outer:last-child { padding-right: 0; }
 #ihrxaykfke .gt_column_spanner { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; overflow-x: hidden; display: inline-block; width: 100%; }
 #ihrxaykfke .gt_spanner_row { border-bottom-style: hidden; }
 #ihrxaykfke .gt_group_heading { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; text-align: left; }
 #ihrxaykfke .gt_empty_group_heading { padding: 0.5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: middle; }
 #ihrxaykfke .gt_from_md> :first-child { margin-top: 0; }
 #ihrxaykfke .gt_from_md> :last-child { margin-bottom: 0; }
 #ihrxaykfke .gt_row { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; margin: 10px; border-top-style: solid; border-top-width: 1px; border-top-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; overflow-x: hidden; }
 #ihrxaykfke .gt_stub { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; }
 #ihrxaykfke .gt_stub_row_group { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; vertical-align: top; }
 #ihrxaykfke .gt_row_group_first td { border-top-width: 2px; }
 #ihrxaykfke .gt_row_group_first th { border-top-width: 2px; }
 #ihrxaykfke .gt_striped { color: #333333; background-color: #F4F4F4; }
 #ihrxaykfke .gt_table_body { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #ihrxaykfke .gt_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #ihrxaykfke .gt_first_summary_row { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; }
 #ihrxaykfke .gt_last_summary_row_top { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #ihrxaykfke .gt_grand_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #ihrxaykfke .gt_first_grand_summary_row_bottom { border-top-style: double; border-top-width: 6px; border-top-color: #D3D3D3; }
 #ihrxaykfke .gt_last_grand_summary_row_top { border-bottom-style: double; border-bottom-width: 6px; border-bottom-color: #D3D3D3; }
 #ihrxaykfke .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #ihrxaykfke .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #ihrxaykfke .gt_left { text-align: left; }
 #ihrxaykfke .gt_center { text-align: center; }
 #ihrxaykfke .gt_right { text-align: right; font-variant-numeric: tabular-nums; }
 #ihrxaykfke .gt_font_normal { font-weight: normal; }
 #ihrxaykfke .gt_font_bold { font-weight: bold; }
 #ihrxaykfke .gt_font_italic { font-style: italic; }
 #ihrxaykfke .gt_super { font-size: 65%; }
 #ihrxaykfke .gt_footnotes { color: font-color(#FFFFFF); background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #ihrxaykfke .gt_footnote { margin: 0px; font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; }
 #ihrxaykfke .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #ihrxaykfke .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #ihrxaykfke .gt_footnote_marks { font-size: 75%; vertical-align: 0.4em; position: initial; }
 #ihrxaykfke .gt_asterisk { font-size: 100%; vertical-align: 0; }
 &#10;</style>

| Q1 — biologic_taken: model vs gold |       |
|------------------------------------|-------|
| metric                             | value |
| precision                          | 0.9   |
| recall                             | 1.0   |
| F1                                 | 0.947 |
| accuracy                           | 0.947 |
| n (gold)                           | 19.0  |

&#10;</div>

On the 19-case golden set, `biologic_taken` scores **F1 = 0.95**
(precision 0.9, recall 1.0; TP/FP/FN/TN = 9/1/0/9) — so the Q1 headline
is well-supported by the gold.

**Q2 — reasons not on a biologic.**

<div id="mmvbdcetbh" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>
#mmvbdcetbh table {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', 'Fira Sans', 'Droid Sans', Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
&#10;#mmvbdcetbh thead, tbody, tfoot, tr, td, th { border-style: none; }
 tr { background-color: transparent; }
#mmvbdcetbh p { margin: 0; padding: 0; }
 #mmvbdcetbh .gt_table { display: table; border-collapse: collapse; line-height: normal; margin-left: auto; margin-right: auto; color: #333333; font-size: 16px; font-weight: normal; font-style: normal; background-color: #FFFFFF; width: auto; border-top-style: solid; border-top-width: 2px; border-top-color: #A8A8A8; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #A8A8A8; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; }
 #mmvbdcetbh .gt_caption { padding-top: 4px; padding-bottom: 4px; }
 #mmvbdcetbh .gt_title { color: #333333; font-size: 125%; font-weight: initial; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; border-bottom-color: #FFFFFF; border-bottom-width: 0; }
 #mmvbdcetbh .gt_subtitle { color: #333333; font-size: 85%; font-weight: initial; padding-top: 3px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; border-top-color: #FFFFFF; border-top-width: 0; }
 #mmvbdcetbh .gt_heading { background-color: #FFFFFF; text-align: center; border-bottom-color: #FFFFFF; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #mmvbdcetbh .gt_bottom_border { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #mmvbdcetbh .gt_col_headings { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #mmvbdcetbh .gt_col_heading { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; overflow-x: hidden; }
 #mmvbdcetbh .gt_column_spanner_outer { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; padding-top: 0; padding-bottom: 0; padding-left: 4px; padding-right: 4px; }
 #mmvbdcetbh .gt_column_spanner_outer:first-child { padding-left: 0; }
 #mmvbdcetbh .gt_column_spanner_outer:last-child { padding-right: 0; }
 #mmvbdcetbh .gt_column_spanner { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; overflow-x: hidden; display: inline-block; width: 100%; }
 #mmvbdcetbh .gt_spanner_row { border-bottom-style: hidden; }
 #mmvbdcetbh .gt_group_heading { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; text-align: left; }
 #mmvbdcetbh .gt_empty_group_heading { padding: 0.5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: middle; }
 #mmvbdcetbh .gt_from_md> :first-child { margin-top: 0; }
 #mmvbdcetbh .gt_from_md> :last-child { margin-bottom: 0; }
 #mmvbdcetbh .gt_row { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; margin: 10px; border-top-style: solid; border-top-width: 1px; border-top-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; overflow-x: hidden; }
 #mmvbdcetbh .gt_stub { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; }
 #mmvbdcetbh .gt_stub_row_group { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; vertical-align: top; }
 #mmvbdcetbh .gt_row_group_first td { border-top-width: 2px; }
 #mmvbdcetbh .gt_row_group_first th { border-top-width: 2px; }
 #mmvbdcetbh .gt_striped { color: #333333; background-color: #F4F4F4; }
 #mmvbdcetbh .gt_table_body { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #mmvbdcetbh .gt_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #mmvbdcetbh .gt_first_summary_row { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; }
 #mmvbdcetbh .gt_last_summary_row_top { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #mmvbdcetbh .gt_grand_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #mmvbdcetbh .gt_first_grand_summary_row_bottom { border-top-style: double; border-top-width: 6px; border-top-color: #D3D3D3; }
 #mmvbdcetbh .gt_last_grand_summary_row_top { border-bottom-style: double; border-bottom-width: 6px; border-bottom-color: #D3D3D3; }
 #mmvbdcetbh .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #mmvbdcetbh .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #mmvbdcetbh .gt_left { text-align: left; }
 #mmvbdcetbh .gt_center { text-align: center; }
 #mmvbdcetbh .gt_right { text-align: right; font-variant-numeric: tabular-nums; }
 #mmvbdcetbh .gt_font_normal { font-weight: normal; }
 #mmvbdcetbh .gt_font_bold { font-weight: bold; }
 #mmvbdcetbh .gt_font_italic { font-style: italic; }
 #mmvbdcetbh .gt_super { font-size: 65%; }
 #mmvbdcetbh .gt_footnotes { color: font-color(#FFFFFF); background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #mmvbdcetbh .gt_footnote { margin: 0px; font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; }
 #mmvbdcetbh .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #mmvbdcetbh .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #mmvbdcetbh .gt_footnote_marks { font-size: 75%; vertical-align: 0.4em; position: initial; }
 #mmvbdcetbh .gt_asterisk { font-size: 100%; vertical-align: 0; }
 &#10;</style>

| Q2 — reasons not on a biologic |          |
|--------------------------------|----------|
| reason                         | patients |
| INSURANCE_PROBLEMS             | 6        |
| PATIENT_FEARS                  | 3        |
| (null)                         | 2        |
| DEFERRED                       | 1        |
| CONTRAINDICATION               | 1        |

&#10;</div>

![Q2 reasons not on a biologic](data/out/plots/q2_reasons.png)

**Q3 — treatments tried before a biologic.**

<div id="uhxeakbmpg" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>
#uhxeakbmpg table {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', 'Fira Sans', 'Droid Sans', Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
&#10;#uhxeakbmpg thead, tbody, tfoot, tr, td, th { border-style: none; }
 tr { background-color: transparent; }
#uhxeakbmpg p { margin: 0; padding: 0; }
 #uhxeakbmpg .gt_table { display: table; border-collapse: collapse; line-height: normal; margin-left: auto; margin-right: auto; color: #333333; font-size: 16px; font-weight: normal; font-style: normal; background-color: #FFFFFF; width: auto; border-top-style: solid; border-top-width: 2px; border-top-color: #A8A8A8; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #A8A8A8; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; }
 #uhxeakbmpg .gt_caption { padding-top: 4px; padding-bottom: 4px; }
 #uhxeakbmpg .gt_title { color: #333333; font-size: 125%; font-weight: initial; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; border-bottom-color: #FFFFFF; border-bottom-width: 0; }
 #uhxeakbmpg .gt_subtitle { color: #333333; font-size: 85%; font-weight: initial; padding-top: 3px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; border-top-color: #FFFFFF; border-top-width: 0; }
 #uhxeakbmpg .gt_heading { background-color: #FFFFFF; text-align: center; border-bottom-color: #FFFFFF; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #uhxeakbmpg .gt_bottom_border { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #uhxeakbmpg .gt_col_headings { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #uhxeakbmpg .gt_col_heading { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; overflow-x: hidden; }
 #uhxeakbmpg .gt_column_spanner_outer { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; padding-top: 0; padding-bottom: 0; padding-left: 4px; padding-right: 4px; }
 #uhxeakbmpg .gt_column_spanner_outer:first-child { padding-left: 0; }
 #uhxeakbmpg .gt_column_spanner_outer:last-child { padding-right: 0; }
 #uhxeakbmpg .gt_column_spanner { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; overflow-x: hidden; display: inline-block; width: 100%; }
 #uhxeakbmpg .gt_spanner_row { border-bottom-style: hidden; }
 #uhxeakbmpg .gt_group_heading { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; text-align: left; }
 #uhxeakbmpg .gt_empty_group_heading { padding: 0.5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: middle; }
 #uhxeakbmpg .gt_from_md> :first-child { margin-top: 0; }
 #uhxeakbmpg .gt_from_md> :last-child { margin-bottom: 0; }
 #uhxeakbmpg .gt_row { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; margin: 10px; border-top-style: solid; border-top-width: 1px; border-top-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; overflow-x: hidden; }
 #uhxeakbmpg .gt_stub { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; }
 #uhxeakbmpg .gt_stub_row_group { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; vertical-align: top; }
 #uhxeakbmpg .gt_row_group_first td { border-top-width: 2px; }
 #uhxeakbmpg .gt_row_group_first th { border-top-width: 2px; }
 #uhxeakbmpg .gt_striped { color: #333333; background-color: #F4F4F4; }
 #uhxeakbmpg .gt_table_body { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #uhxeakbmpg .gt_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #uhxeakbmpg .gt_first_summary_row { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; }
 #uhxeakbmpg .gt_last_summary_row_top { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #uhxeakbmpg .gt_grand_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #uhxeakbmpg .gt_first_grand_summary_row_bottom { border-top-style: double; border-top-width: 6px; border-top-color: #D3D3D3; }
 #uhxeakbmpg .gt_last_grand_summary_row_top { border-bottom-style: double; border-bottom-width: 6px; border-bottom-color: #D3D3D3; }
 #uhxeakbmpg .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #uhxeakbmpg .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #uhxeakbmpg .gt_left { text-align: left; }
 #uhxeakbmpg .gt_center { text-align: center; }
 #uhxeakbmpg .gt_right { text-align: right; font-variant-numeric: tabular-nums; }
 #uhxeakbmpg .gt_font_normal { font-weight: normal; }
 #uhxeakbmpg .gt_font_bold { font-weight: bold; }
 #uhxeakbmpg .gt_font_italic { font-style: italic; }
 #uhxeakbmpg .gt_super { font-size: 65%; }
 #uhxeakbmpg .gt_footnotes { color: font-color(#FFFFFF); background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #uhxeakbmpg .gt_footnote { margin: 0px; font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; }
 #uhxeakbmpg .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #uhxeakbmpg .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #uhxeakbmpg .gt_footnote_marks { font-size: 75%; vertical-align: 0.4em; position: initial; }
 #uhxeakbmpg .gt_asterisk { font-size: 100%; vertical-align: 0; }
 &#10;</style>

| Q3 — treatments tried before a biologic |          |
|-----------------------------------------|----------|
| treatment_class                         | mentions |
| conventional_therapy                    | 26       |
| conventional                            | 23       |
| aminosalicylate                         | 22       |
| corticosteroid                          | 16       |
| Immunosuppressant                       | 11       |
| 5-ASA                                   | 10       |
| Corticosteroid                          | 7        |
| immunomodulator                         | 6        |
| immunosuppressant                       | 4        |
| biologic                                | 2        |
| Diabetes medication                     | 1        |
| hormonal therapy                        | 1        |
| analgesic                               | 1        |
| hormone replacement                     | 1        |
| antibiotic                              | 1        |

&#10;</div>

![Q3 treatments before a
biologic](data/out/plots/q3_before_biologic.png)

**Q4 — referral pathway length (steps to a biologic-prescribing
specialist).**

> **Caveat.** The literal “GP” node (`primary_care_contact`) appears in
> only 5/50 predicted pathways, so a strict GP→prescriber count isn’t
> representative. We count steps from the journey **start** (or
> `primary_care_contact` where present) to `biologic_recommended`
> (present in 50/50) — the point a biologic-prescribing specialist is
> reached. Under-emission of the GP node is a prompt-fix candidate (see
> `docs/TODO.md`). Per-case journey graphs:
> `data/out/referral_pathway_P*.html`.

<div id="lepgvnovpv" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>
#lepgvnovpv table {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', 'Fira Sans', 'Droid Sans', Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
&#10;#lepgvnovpv thead, tbody, tfoot, tr, td, th { border-style: none; }
 tr { background-color: transparent; }
#lepgvnovpv p { margin: 0; padding: 0; }
 #lepgvnovpv .gt_table { display: table; border-collapse: collapse; line-height: normal; margin-left: auto; margin-right: auto; color: #333333; font-size: 16px; font-weight: normal; font-style: normal; background-color: #FFFFFF; width: auto; border-top-style: solid; border-top-width: 2px; border-top-color: #A8A8A8; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #A8A8A8; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; }
 #lepgvnovpv .gt_caption { padding-top: 4px; padding-bottom: 4px; }
 #lepgvnovpv .gt_title { color: #333333; font-size: 125%; font-weight: initial; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; border-bottom-color: #FFFFFF; border-bottom-width: 0; }
 #lepgvnovpv .gt_subtitle { color: #333333; font-size: 85%; font-weight: initial; padding-top: 3px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; border-top-color: #FFFFFF; border-top-width: 0; }
 #lepgvnovpv .gt_heading { background-color: #FFFFFF; text-align: center; border-bottom-color: #FFFFFF; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #lepgvnovpv .gt_bottom_border { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #lepgvnovpv .gt_col_headings { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #lepgvnovpv .gt_col_heading { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; overflow-x: hidden; }
 #lepgvnovpv .gt_column_spanner_outer { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; padding-top: 0; padding-bottom: 0; padding-left: 4px; padding-right: 4px; }
 #lepgvnovpv .gt_column_spanner_outer:first-child { padding-left: 0; }
 #lepgvnovpv .gt_column_spanner_outer:last-child { padding-right: 0; }
 #lepgvnovpv .gt_column_spanner { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; overflow-x: hidden; display: inline-block; width: 100%; }
 #lepgvnovpv .gt_spanner_row { border-bottom-style: hidden; }
 #lepgvnovpv .gt_group_heading { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; text-align: left; }
 #lepgvnovpv .gt_empty_group_heading { padding: 0.5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: middle; }
 #lepgvnovpv .gt_from_md> :first-child { margin-top: 0; }
 #lepgvnovpv .gt_from_md> :last-child { margin-bottom: 0; }
 #lepgvnovpv .gt_row { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; margin: 10px; border-top-style: solid; border-top-width: 1px; border-top-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; overflow-x: hidden; }
 #lepgvnovpv .gt_stub { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; }
 #lepgvnovpv .gt_stub_row_group { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; vertical-align: top; }
 #lepgvnovpv .gt_row_group_first td { border-top-width: 2px; }
 #lepgvnovpv .gt_row_group_first th { border-top-width: 2px; }
 #lepgvnovpv .gt_striped { color: #333333; background-color: #F4F4F4; }
 #lepgvnovpv .gt_table_body { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #lepgvnovpv .gt_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #lepgvnovpv .gt_first_summary_row { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; }
 #lepgvnovpv .gt_last_summary_row_top { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #lepgvnovpv .gt_grand_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #lepgvnovpv .gt_first_grand_summary_row_bottom { border-top-style: double; border-top-width: 6px; border-top-color: #D3D3D3; }
 #lepgvnovpv .gt_last_grand_summary_row_top { border-bottom-style: double; border-bottom-width: 6px; border-bottom-color: #D3D3D3; }
 #lepgvnovpv .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #lepgvnovpv .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #lepgvnovpv .gt_left { text-align: left; }
 #lepgvnovpv .gt_center { text-align: center; }
 #lepgvnovpv .gt_right { text-align: right; font-variant-numeric: tabular-nums; }
 #lepgvnovpv .gt_font_normal { font-weight: normal; }
 #lepgvnovpv .gt_font_bold { font-weight: bold; }
 #lepgvnovpv .gt_font_italic { font-style: italic; }
 #lepgvnovpv .gt_super { font-size: 65%; }
 #lepgvnovpv .gt_footnotes { color: font-color(#FFFFFF); background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #lepgvnovpv .gt_footnote { margin: 0px; font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; }
 #lepgvnovpv .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #lepgvnovpv .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #lepgvnovpv .gt_footnote_marks { font-size: 75%; vertical-align: 0.4em; position: initial; }
 #lepgvnovpv .gt_asterisk { font-size: 100%; vertical-align: 0; }
 &#10;</style>

| Q4 — steps to biologic recommendation |       |
|---------------------------------------|-------|
| stat                                  | steps |
| count                                 | 50.0  |
| min                                   | 6.0   |
| 50%                                   | 9.0   |
| max                                   | 13.0  |
| mean                                  | 8.9   |

&#10;</div>

    ![Q4 steps to biologic recommendation](data/out/plots/q4_steps.png)

A typical journey is **~9 steps** from start to a biologic
recommendation (range 6–13, n=50).

**Churn handling matters here.** Be explicit about:

- How many journeys in your output look truncated vs. complete, and how
  you decided.
- How you separated “biologic not mentioned” from “biologic discussed
  and rejected” from “patient churned before reaching that point.”
- Which of the four answers are most and least trustworthy given the
  churn distribution, and why.

<div id="izkmaraoao" style="padding-left:0px;padding-right:0px;padding-top:10px;padding-bottom:10px;overflow-x:auto;overflow-y:auto;width:auto;height:auto;">
<style>
#izkmaraoao table {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', 'Fira Sans', 'Droid Sans', Arial, sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }
&#10;#izkmaraoao thead, tbody, tfoot, tr, td, th { border-style: none; }
 tr { background-color: transparent; }
#izkmaraoao p { margin: 0; padding: 0; }
 #izkmaraoao .gt_table { display: table; border-collapse: collapse; line-height: normal; margin-left: auto; margin-right: auto; color: #333333; font-size: 16px; font-weight: normal; font-style: normal; background-color: #FFFFFF; width: auto; border-top-style: solid; border-top-width: 2px; border-top-color: #A8A8A8; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #A8A8A8; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; }
 #izkmaraoao .gt_caption { padding-top: 4px; padding-bottom: 4px; }
 #izkmaraoao .gt_title { color: #333333; font-size: 125%; font-weight: initial; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; border-bottom-color: #FFFFFF; border-bottom-width: 0; }
 #izkmaraoao .gt_subtitle { color: #333333; font-size: 85%; font-weight: initial; padding-top: 3px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; border-top-color: #FFFFFF; border-top-width: 0; }
 #izkmaraoao .gt_heading { background-color: #FFFFFF; text-align: center; border-bottom-color: #FFFFFF; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #izkmaraoao .gt_bottom_border { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #izkmaraoao .gt_col_headings { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; }
 #izkmaraoao .gt_col_heading { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; padding-left: 5px; padding-right: 5px; overflow-x: hidden; }
 #izkmaraoao .gt_column_spanner_outer { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: normal; text-transform: inherit; padding-top: 0; padding-bottom: 0; padding-left: 4px; padding-right: 4px; }
 #izkmaraoao .gt_column_spanner_outer:first-child { padding-left: 0; }
 #izkmaraoao .gt_column_spanner_outer:last-child { padding-right: 0; }
 #izkmaraoao .gt_column_spanner { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: bottom; padding-top: 5px; padding-bottom: 5px; overflow-x: hidden; display: inline-block; width: 100%; }
 #izkmaraoao .gt_spanner_row { border-bottom-style: hidden; }
 #izkmaraoao .gt_group_heading { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; text-align: left; }
 #izkmaraoao .gt_empty_group_heading { padding: 0.5px; color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; vertical-align: middle; }
 #izkmaraoao .gt_from_md> :first-child { margin-top: 0; }
 #izkmaraoao .gt_from_md> :last-child { margin-bottom: 0; }
 #izkmaraoao .gt_row { padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; margin: 10px; border-top-style: solid; border-top-width: 1px; border-top-color: #D3D3D3; border-left-style: none; border-left-width: 1px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 1px; border-right-color: #D3D3D3; vertical-align: middle; overflow-x: hidden; }
 #izkmaraoao .gt_stub { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; }
 #izkmaraoao .gt_stub_row_group { color: #333333; background-color: #FFFFFF; font-size: 100%; font-weight: initial; text-transform: inherit; border-right-style: solid; border-right-width: 2px; border-right-color: #D3D3D3; padding-left: 5px; padding-right: 5px; vertical-align: top; }
 #izkmaraoao .gt_row_group_first td { border-top-width: 2px; }
 #izkmaraoao .gt_row_group_first th { border-top-width: 2px; }
 #izkmaraoao .gt_striped { color: #333333; background-color: #F4F4F4; }
 #izkmaraoao .gt_table_body { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #izkmaraoao .gt_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #izkmaraoao .gt_first_summary_row { border-top-style: solid; border-top-width: 2px; border-top-color: #D3D3D3; }
 #izkmaraoao .gt_last_summary_row_top { border-bottom-style: solid; border-bottom-width: 2px; border-bottom-color: #D3D3D3; }
 #izkmaraoao .gt_grand_summary_row { color: #333333; background-color: #FFFFFF; text-transform: inherit; padding-top: 8px; padding-bottom: 8px; padding-left: 5px; padding-right: 5px; }
 #izkmaraoao .gt_first_grand_summary_row_bottom { border-top-style: double; border-top-width: 6px; border-top-color: #D3D3D3; }
 #izkmaraoao .gt_last_grand_summary_row_top { border-bottom-style: double; border-bottom-width: 6px; border-bottom-color: #D3D3D3; }
 #izkmaraoao .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #izkmaraoao .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #izkmaraoao .gt_left { text-align: left; }
 #izkmaraoao .gt_center { text-align: center; }
 #izkmaraoao .gt_right { text-align: right; font-variant-numeric: tabular-nums; }
 #izkmaraoao .gt_font_normal { font-weight: normal; }
 #izkmaraoao .gt_font_bold { font-weight: bold; }
 #izkmaraoao .gt_font_italic { font-style: italic; }
 #izkmaraoao .gt_super { font-size: 65%; }
 #izkmaraoao .gt_footnotes { color: font-color(#FFFFFF); background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #izkmaraoao .gt_footnote { margin: 0px; font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; }
 #izkmaraoao .gt_sourcenotes { color: #333333; background-color: #FFFFFF; border-bottom-style: none; border-bottom-width: 2px; border-bottom-color: #D3D3D3; border-left-style: none; border-left-width: 2px; border-left-color: #D3D3D3; border-right-style: none; border-right-width: 2px; border-right-color: #D3D3D3; }
 #izkmaraoao .gt_sourcenote { font-size: 90%; padding-top: 4px; padding-bottom: 4px; padding-left: 5px; padding-right: 5px; text-align: left; }
 #izkmaraoao .gt_footnote_marks { font-size: 75%; vertical-align: 0.4em; position: initial; }
 #izkmaraoao .gt_asterisk { font-size: 100%; vertical-align: 0; }
 &#10;</style>

| Churn — three-way split            |          |
|------------------------------------|----------|
| state                              | patients |
| biologic not mentioned (absence)   | 0        |
| discussed but not taken (negation) | 13       |
| churned / truncated                | 0        |

&#10;</div>

The model flagged `churn = true` for only **0/50** patient(s). Manual
review of the flagged/edge cases (`docs/TO_REVIEW.md`) found churn
detection unreliable in both directions — a false positive (P016) and a
false negative (P049) — because truncation is a lexical/structural
property of the transcript’s *end* that the narrative under-determines.
**Q1 and Q3 are the most trustworthy** answers (they depend on facts
stated early); **Q4 is the least** (it depends on the full pathway
surviving, and on the under-emitted GP node).

### Churn — definition & handling

**Definition.** The spec never defines the “interview”. We read it as
the patient’s interaction with the Mama Health AI companion app —
patients describe their doctors in the *third person*, so they’re
narrating *to the app*, not conversing with a clinician. **Churn is
therefore disengagement from that app interaction**, which in the data
shows up as a transcript that stops early. The spec backs this:
*“patients disengage partway through their interview — they churn —
leaving us with truncated journeys”*, and the transcripts vary in
*“completeness… some cut off mid-journey”* (with a worked “incomplete,
likely churn” example).

**One flag, not two.** Because “churned” and “incomplete journey” are
the *same* signal under this reading, we collapse them into a single
`churn` field (ground truth `…_v4.ods` drops `incomplete_journey`).
`churn = true` when there’s evidence of **(a)** disengagement from the
app interaction, or **(b)** a truncated / cut-off / vague narrative.
Signals: completeness, cut off mid-journey, truncation, vagueness.

**Why this matters for the answers.** `churn` is the *truncation* state
that, with `biologic_not_mentioned` (absence) and a
discussed-but-not-taken biologic (negation), gives the three-way split
the analysis needs — “not mentioned” vs “discussed and rejected” vs
“churned before we could find out”. It stays a judgement call with
residual uncertainty, but a single honest flag beats splitting two
overlapping ones.

## Evaluation Criteria

- **Schema judgment.** Does your Pydantic model capture the real shape
  of the problem, including its messiness and uncertainty?
- **Pipeline engineering.** Clean, typed code, sensible error handling,
  defensible choices on prompting, retries, validation, reproducibility.
- **Uncertainty handling.** Do churn, ambiguity, and absent information
  show up as first-class signals in your output, or do they silently
  collapse into nulls?
- **Evaluation mindset.** Do you know whether your pipeline is actually
  working, and how you know?
- **Communication.** A README where a reader can understand your
  assumptions, tradeoffs, and limits in under 5 minutes.

We’re **not** looking for: - A perfect extractor — the data is
intentionally hard. - Production-grade architecture. - A sprawling
business-insights writeup.

## Deliverables

A link to your forked, completed GitHub repo containing:

1.  Source code in `src/`.
2.  Tests in `tests/`.
3.  `requirements.txt`.
4.  A **`README.md`** with:
    - Your four business answers (brief, with caveats).
    - A pipeline design section — schema choices, prompting approach,
      error handling, reproducibility.
    - Your evaluation approach and what it surfaced.
    - Churn / limitations discussion.
    - Your “where I used AI” note.

## Optional stretch tasks

Only if you have spare time. We’d rather see a tight core than a bloated
stretch:

1.  **Multi-stage or chain-of-thought prompts** with inspectable
    intermediate artifacts.
2.  **Confidence scoring per field**, either self-reported by the LLM or
    derived from consistency across samples.
3.  **Open-source model** — swap in a local model (Qwen, Llama, etc.)
    for one stage via `litellm` and compare quality/latency/cost.
4.  **Sankey or pathway visualization** for the referral journey.
5.  **Dockerfile** for reproducibility.

I’ve attempted (4) as a way of answering business question (4) on
referral pathways.

## Next Steps

With more time, after the core is complete:

- **Split the single system prompt into multiple focused prompts run
  concurrently.** This version deliberately uses one prompt; a later
  iteration would break extraction into per-section prompts
  (e.g. biologic funnel, treatment history, referral pathway) run in
  parallel — better per-field accuracy and inspectable intermediate
  artifacts, at the cost of more calls and orchestration.
- **A telemetry feature for optimisation.** Per-call usage is currently
  logged (tokens, cost, cached tokens — see
  [docs/TELEMETRY.md](docs/TELEMETRY.md)); with more time I’d surface it
  as a first-class artifact (a structured per-run metrics file + plots)
  to track cost/latency/cache-hit rate and tune the pipeline at scale.
- **Try a larger Gemini model in production.** This version uses
  `gemini-2.5-flash-lite` (cheap, fast for iteration). With more time
  I’d evaluate a more capable model (e.g. `gemini-2.5-flash` / `pro`)
  for extraction quality, weighed against its free-tier **request/token
  rate limits** (the ~20 calls/day cap that drove the chunking design)
  and cost.
- **Deep dive on cyclical journey patterns.** The `referral_pathway`
  initially flattened recurrence (each phase emitted once); the prompt
  now asks the model to repeat steps when phases recur. A proper
  follow-up would analyse the *cyclicity* itself — how many biologics
  patients cycle through, repeated relapse / loss-of-response / switch
  loops, time-to-switch — and classify journeys as genuinely cyclic vs
  linear (the recurrence is also recoverable from `treatment_records`).

## Where I used AI

TBA

## Usage

Run the extraction pipeline via the `src/main.py` CLI (python-fire).
**By default it extracts all 50 transcripts in chunks of 10 → 5 API
calls**, sized to the Gemini free tier’s ~20 requests/day cap (taken as
a fixed constraint; 50 one-at-a-time calls would exceed it).

``` bash
uv run python src/main.py                          # all 50, chunks of 10 (5 calls)
uv run python src/main.py --limit=10               # run 1 only: P001–P010
uv run python src/main.py --limit=10 --offset=10   # run 2: P011–P020 (no re-run of earlier chunks)
```

| Flag | Default | Purpose |
|----|----|----|
| `--model` | `gemini/gemini-2.5-flash-lite` | swap model (Gemini ↔ local Ollama, e.g. `ollama_chat/qwen3:30b-a3b`) |
| `--limit` | all | slice size — run one chunk for testing / incremental runs |
| `--offset` | `0` | which slice — incremental runs without redoing earlier chunks |
| `--chunk-size` | `10` | transcripts per API call |
| `--out-dir` | `data/out` | route test runs to `data/out/tests` so they don’t clobber production |

The post-extraction EDA (this README’s tables/plots) is generated by
`uv run quarto render README.qmd`, which reads only `data/out/` —
**independent of the Gemini API**. Each chunk persists its predictions
(one JSON per patient) as soon as it validates, so a completed chunk is
durable and `--offset` lets you resume/retry without re-spending calls.
Per-call telemetry (tokens, cost) is logged to `logs/extract.log`.

## Data handling & privacy

> ⚠️ **This repo commits `data/in/` and `data/out/` (model inputs and
> outputs) to git — which you should NOT do in a production system.**
> Real patient interview data and extracted records are **personal /
> special-category health data** under GDPR and must never be pushed to
> GitHub or any external version control — PII exposure, data-residency,
> retention, and access-control all forbid it.
>
> It is acceptable **here only** because the dataset is **synthetic**,
> the repo is **private**, and committing the data + outputs makes this
> **internal job-interview take-home auditable** end-to-end by the
> reviewer. In production, inputs/outputs would live in secure storage
> under a data-processing agreement and **only code** would be
> version-controlled. See [docs/QUESTIONS.md](docs/QUESTIONS.md) \#7.

## Requirements

Dev environment requirements and setup — Python 3.14 (via uv), a
`GEMINI_API_KEY`, and the VS Code + Claude Code extension diff-review
workflow — are documented once in [docs/SETUP.md](docs/SETUP.md); this
README only links there to avoid duplication.

Further documentation is provided as follows:

- [CLAUDE.md](CLAUDE.md) for Claude Code project instructions.

- [SETUP.md](docs/SETUP.md) for installation and usage guide for users
  and devs.

- \[.claude/skills\] Agent Skills formatted skills for CC to use
  specific to this project.
