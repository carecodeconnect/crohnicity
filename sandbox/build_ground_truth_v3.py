"""One-shot cleanup: interviews_ground_truth_v2.ods -> interviews_ground_truth_v3.ods.

Two deterministic fixes (annotations otherwise preserved), written with column widths +
autofilter:
  1. to_review -> numeric 1/0 (consistent with the other boolean columns).
  2. Misplaced PROSE in the reasons columns -> evidence_notes; blank those cells. Valid enums
     and status markers are UPPERCASE, so any lowercase letter flags free text to move.
Kept in sandbox/ as a record of a reviewed transformation.
Run: uv run python sandbox/build_ground_truth_v3.py
"""

from pathlib import Path

import pandas as pd
from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TableCellProperties, TableColumnProperties, TextProperties
from odf.table import (
    DatabaseRange,
    DatabaseRanges,
    Table,
    TableCell,
    TableColumn,
    TableRow,
)
from odf.text import P

ROOT = Path.cwd()
ROOT = ROOT if (ROOT / "src").exists() else ROOT.parent
DATA_IN = ROOT / "data" / "in"
src_ods = DATA_IN / "interviews_ground_truth_v2.ods"
dst_ods = DATA_IN / "interviews_ground_truth_v3.ods"
SHEET = "ground_truth"

V2_ORDER = [
    "patient_id",
    "interview_transcript",
    "to_review",
    "churn",
    "incomplete_journey",
    "gender",
    "age",
    "biologic_prescribed",
    "biologic_taken",
    "biologic_not_mentioned",
    "biologic_type",
    "reasons_for_biologic_prescribed",
    "reasons_for_biologic_not_taken",
    "comorbid_conditions",
    "treatment_records",
    "treatment_outcome",
    "referral_pathway",
    "evidence_notes",
]
WRAP_COLS = {
    "interview_transcript",
    "treatment_records",
    "referral_pathway",
    "evidence_notes",
}
NUMERIC_COLS = {
    "to_review",
    "churn",
    "incomplete_journey",
    "biologic_prescribed",
    "biologic_taken",
    "biologic_not_mentioned",
}
REASON_COLS = ("reasons_for_biologic_prescribed", "reasons_for_biologic_not_taken")

df = pd.read_excel(src_ods, engine="odf")

# Fix 1: standardise to_review to numeric 1/0
df["to_review"] = df["to_review"].astype(float)

# Fix 2: move misplaced prose out of the reasons columns into evidence_notes; blank those cells
text_cols = [c for c in V2_ORDER if c not in NUMERIC_COLS and c != "patient_id"]
df[text_cols] = df[text_cols].astype("object")


def is_prose(v):
    return isinstance(v, str) and any(c.islower() for c in v)


for col in REASON_COLS:
    for i in df.index[df[col].map(is_prose)]:
        snippet = df.at[i, col]
        ev = df.at[i, "evidence_notes"]
        df.at[i, "evidence_notes"] = snippet if pd.isna(ev) else f"{ev} | {snippet}"
        df.at[i, col] = pd.NA

df = df[V2_ORDER]


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
    cs.addElement(
        TableColumnProperties(columnwidth=f"{width_cm(df[name], name):.2f}cm")
    )
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
            cell = (
                TableCell(valuetype="string", stylename=wrap)
                if name in WRAP_COLS
                else TableCell(valuetype="string")
            )
            cell.addElement(P(text=str(v)))
            trow.addElement(cell)
    table.addElement(trow)
doc.spreadsheet.addElement(table)

addr = f"{SHEET}.A1:{col_letter(len(df.columns))}{len(df) + 1}"
ranges = DatabaseRanges()
ranges.addElement(
    DatabaseRange(
        name="__Anonymous_Sheet_DB__0",
        targetrangeaddress=addr,
        displayfilterbuttons="true",
    )
)
doc.spreadsheet.addElement(ranges)
doc.save(str(dst_ods))
print(f"wrote {df.shape[0]} rows x {df.shape[1]} cols -> {dst_ods}")
