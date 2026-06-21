"""One-shot: interviews_ground_truth_v3.ods -> interviews_ground_truth_v4.ods.

Single change (all other annotations + formatting preserved): collapse `incomplete_journey` into
`churn` and drop the `incomplete_journey` column. Per the task spec, churn = the interview is
truncated / cut off mid-journey (disengagement from the Mama Health app interaction), so a
"truncated" flag and a "churned" flag are the same signal — see README "Churn".

Combine is a logical OR with NaN preserved: churn=1 if either flag was 1 (so P049, the one
incomplete_journey=1 row, becomes churn=1), 0 if either was 0, blank if both were unannotated.
Kept in sandbox/ as a record of a reviewed transformation.
Run: uv run python sandbox/build_ground_truth_v4.py
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
src_ods = DATA_IN / "interviews_ground_truth_v3.ods"
dst_ods = DATA_IN / "interviews_ground_truth_v4.ods"
SHEET = "ground_truth"

V4_ORDER = [
    "patient_id", "interview_transcript", "to_review", "churn",
    "gender", "age", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned",
    "biologic_type", "reasons_for_biologic_prescribed", "reasons_for_biologic_not_taken",
    "comorbid_conditions", "treatment_records", "treatment_outcome", "referral_pathway",
    "evidence_notes",
]
WRAP_COLS = {"interview_transcript", "treatment_records", "referral_pathway", "evidence_notes"}
NUMERIC_COLS = {"to_review", "churn", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned"}

df = pd.read_excel(src_ods, engine="odf")


def combined_churn(row):
    """OR churn with incomplete_journey; keep blank only if both are unannotated."""
    vals = [row["churn"], row["incomplete_journey"]]
    if any(v == 1 for v in vals):
        return 1.0
    if any(v == 0 for v in vals):
        return 0.0
    return pd.NA


df["churn"] = df.apply(combined_churn, axis=1)
df = df[V4_ORDER]


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
