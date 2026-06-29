"""One-shot: interviews_ground_truth_v6.ods -> interviews_ground_truth_v7.ods.

Prerequisite — copy the prior version first so _v7 starts as an exact clone of _v6:
    cp data/in/interviews_ground_truth_v6.ods data/in/interviews_ground_truth_v7.ods
This script then READS and WRITES _v7.ods, leaving _v6.ods untouched as the prior version. (As with
every prior version, the frozen header is re-applied by hand: View > Freeze Rows.)

Single change (all other annotations preserved): set `reasons_for_biologic_not_taken = BIOLOGIC_TAKEN`
for every case where a biologic was actually taken (`biologic_taken == 1`) — a logical consequence of
having taken one, independent of the `to_review` flag (in practice only annotated rows have it set). The schema's
`reasons_for_biologic_not_taken` is a NEVER-EMPTY list (SCHEMA v0.8); a biologic-taken patient has no
"not taken" reason, so the explicit `BIOLOGIC_TAKEN` value replaces the empty / `NOT_APPLICABLE`
placeholder, keeping the field trackable (an empty list is indistinguishable from a missing value).
Derived from the boolean, so it is robust to whatever string the cell currently holds.
Follows the odfpy rebuild recipe of build_ground_truth_v2..v6.py.
Run: uv run python sandbox/build_ground_truth_v7.py
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
src_ods = DATA_IN / "interviews_ground_truth_v7.ods"
dst_ods = DATA_IN / "interviews_ground_truth_v7.ods"
SHEET = "ground_truth"

V_ORDER = [
    "patient_id", "interview_transcript", "to_review", "churn",
    "gender", "age", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned",
    "biologic_type", "reasons_for_biologic_prescribed", "reasons_for_biologic_not_taken",
    "comorbid_conditions", "treatment_records", "treatment_outcome", "referral_pathway",
    "evidence_notes",
]
WRAP_COLS = {"interview_transcript", "treatment_records", "referral_pathway", "evidence_notes"}
NUMERIC_COLS = {"to_review", "churn", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned"}

df = pd.read_excel(src_ods, engine="odf")
df = df[V_ORDER]

# A biologic-taken patient has no "not taken" reason -> the explicit, never-empty BIOLOGIC_TAKEN.
taken = df["biologic_taken"] == 1
df["reasons_for_biologic_not_taken"] = df["reasons_for_biologic_not_taken"].astype("object")
df.loc[taken, "reasons_for_biologic_not_taken"] = "BIOLOGIC_TAKEN"
print(f"set BIOLOGIC_TAKEN for {int(taken.sum())} biologic-taken cases: {list(df.loc[taken, 'patient_id'])}")


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
