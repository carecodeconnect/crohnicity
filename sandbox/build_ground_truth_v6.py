"""One-shot: complete P047 in interviews_ground_truth_v6.ods (in place).

Prerequisite — copy the prior version first so _v6 starts as an exact clone of _v5:
    cp data/in/interviews_ground_truth_v5.ods data/in/interviews_ground_truth_v6.ods
This script then READS and WRITES _v6.ods, leaving _v5.ods untouched as the prior version. (As
with every prior version, the frozen header is re-applied by hand: View > Freeze Rows.)

Single change (all other annotations preserved): complete the previously-empty
annotation columns for **P047** so it becomes a fully-reviewed gold case. P047 is the edge case
where the model over-detected `biologic_prescribed=True` on a transcript that mentions no biologic
at all (Donna — prednisone/mesalamine/methotrexate only); the human review set `to_review=1`,
`biologic_not_mentioned=1`, `biologic_prescribed=0`, and `churn=0` (the transcript ends on a
coherent emotional close, "...not worry about mom...", an intentional trailing-off, not a
mid-thought cut-off). This script fills the remaining empty columns from that same transcript.

Only writes into P047's EMPTY cells, so existing annotations are preserved. Follows the odfpy
rebuild recipe of build_ground_truth_v2/v3/v4.py (column widths + autofilter re-applied; the frozen
header is the one manual step: View > Freeze Rows). Kept in sandbox/ as a record.
Run: uv run python sandbox/build_ground_truth_v6.py
"""

from pathlib import Path

import pandas as pd
from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TableCellProperties, TableColumnProperties, TextProperties
from odf.table import DatabaseRange, DatabaseRanges, Table, TableCell, TableColumn, TableRow
from odf.text import P

ROOT = Path.cwd()
ROOT = ROOT if (ROOT / "src").exists() else ROOT.parent
DATA_IN = ROOT / "data" / "in"
src_ods = DATA_IN / "interviews_ground_truth_v6.ods"
dst_ods = DATA_IN / "interviews_ground_truth_v6.ods"
SHEET = "ground_truth"

V6_ORDER = [
    "patient_id", "interview_transcript", "to_review", "churn",
    "gender", "age", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned",
    "biologic_type", "reasons_for_biologic_prescribed", "reasons_for_biologic_not_taken",
    "comorbid_conditions", "treatment_records", "treatment_outcome", "referral_pathway",
    "evidence_notes",
]
WRAP_COLS = {"interview_transcript", "treatment_records", "referral_pathway", "evidence_notes"}
NUMERIC_COLS = {"to_review", "churn", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned"}

# P047's empty columns, completed from the transcript (conventional therapy only; no biologic).
P047_FILL = {
    "comorbid_conditions": "HYPOTHYROIDISM, DEPRESSION",
    "treatment_records": (
        "prednisone | corticosteroid | PARTIAL | weight gain\n"
        "mesalamine | 5-asa | UNKNOWN | \n"
        "methotrexate | immunomodulator | PARTIAL | "
    ),
    "treatment_outcome": "ONGOING",
    "referral_pathway": (
        "symptom_onset -> misdiagnosis(IBS) -> diagnostic_delay -> specialist_referral -> "
        "diagnostic_testing -> crohns_diagnosis -> conventional_therapy(prednisone) -> "
        "adverse_reaction -> conventional_therapy(mesalamine) -> "
        "conventional_therapy(methotrexate) -> unresolved"
    ),
    "evidence_notes": (
        "No biologic mentioned, prescribed, or offered — conventional therapy only (prednisone, "
        "mesalamine, methotrexate), 5 months post-diagnosis. Edge case: the model over-detected "
        "biologic_prescribed=True here. churn=0 — ends on a coherent emotional close "
        "('...not worry about mom...'), an intentional trailing-off, not a mid-thought cut-off."
    ),
}

df = pd.read_excel(src_ods, engine="odf")
df = df[V6_ORDER]

mask = df["patient_id"] == "P047"
assert mask.sum() == 1, "expected exactly one P047 row"
for col, val in P047_FILL.items():
    df[col] = df[col].astype("object")  # all-NaN columns read as float64; allow string cells
    if df.loc[mask, col].isna().all():  # only write into empty cells
        df.loc[mask, col] = val
    else:
        print(f"skip {col}: P047 already populated ({df.loc[mask, col].iloc[0]!r})")


def col_letter(n):
    s = ""
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def width_cm(series, name):
    longest = max([len(str(name))] + [len(str(v)) for v in series if pd.notna(v)])
    return min(max(longest * 0.20, 2.5), 14.0)


doc = OpenDocumentSpreadsheet()
bold = Style(name="hdr", family="table-cell")
bold.addElement(TextProperties(fontweight="bold"))
doc.automaticstyles.addElement(bold)
wrap = Style(name="wrap", family="table-cell")
wrap.addElement(TableCellProperties(wrapoption="wrap", verticalalign="top"))
doc.automaticstyles.addElement(wrap)

table = Table(name=SHEET)
for name in df.columns:
    cs = Style(name=f"co-{name}", family="table-column")
    cs.addElement(TableColumnProperties(columnwidth=f"{width_cm(df[name], name):.2f}cm"))
    doc.automaticstyles.addElement(cs)
    table.addElement(TableColumn(stylename=cs))

hrow = TableRow()
for name in df.columns:
    cell = TableCell(valuetype="string", stylename=bold)
    cell.addElement(P(text=name))
    hrow.addElement(cell)
table.addElement(hrow)

for _, row in df.iterrows():
    trow = TableRow()
    for name in df.columns:
        v = row[name]
        if pd.isna(v):
            trow.addElement(TableCell())
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            trow.addElement(TableCell(valuetype="float", value=float(v)))
        else:
            cell = TableCell(valuetype="string", stylename=wrap) if name in WRAP_COLS else TableCell(valuetype="string")
            cell.addElement(P(text=str(v)))
            trow.addElement(cell)
    table.addElement(trow)
doc.spreadsheet.addElement(table)

addr = f"{SHEET}.A1:{col_letter(len(df.columns))}{len(df) + 1}"
ranges = DatabaseRanges()
ranges.addElement(DatabaseRange(name="__Anonymous_Sheet_DB__0", targetrangeaddress=addr, displayfilterbuttons="true"))
doc.spreadsheet.addElement(ranges)
doc.save(str(dst_ods))
print(f"wrote {df.shape[0]} rows x {df.shape[1]} cols -> {dst_ods}")
