"""One-shot migration: interviews_ground_truth.ods (v1) -> interviews_ground_truth_v2.ods.

Read -> rename/add/reorder -> fill ONLY empty cells (annotations preserved) -> write with
column widths + autofilter. Kept in sandbox/ as a record of a reviewed transformation.
Run: uv run python sandbox/build_ground_truth_v2.py
"""

import sys
from pathlib import Path

import pandas as pd
from odf.opendocument import OpenDocumentSpreadsheet
from odf.style import Style, TableCellProperties, TableColumnProperties, TextProperties
from odf.table import DatabaseRange, DatabaseRanges, Table, TableCell, TableColumn, TableRow
from odf.text import P

ROOT = Path.cwd()
ROOT = ROOT if (ROOT / "src").exists() else ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
from referral_pathway_analysis import PATHWAYS  # reviewed candidate chains, P001-P010

DATA_IN = ROOT / "data" / "in"
src_ods = DATA_IN / "interviews_ground_truth.ods"
dst_ods = DATA_IN / "interviews_ground_truth_v2.ods"
SHEET = "ground_truth"

# One-time bootstrap for to_review; thereafter to_review IN THE SHEET is the source of truth
# (src/splits.py derives validation/holdout by reading it). Re-running preserves an existing flag.
VALIDATION_SEED = [
    "P001", "P002", "P003", "P004", "P005", "P006", "P007", "P008", "P009", "P010",
    "P016", "P017", "P027", "P032", "P035", "P044", "P045", "P048", "P049", "P050",
]
DEMOGRAPHICS = {  # self-reported, from transcripts
    "P001": ("female", 34), "P002": ("male", 42), "P003": ("female", 28), "P004": ("male", 55),
    "P005": ("female", 31), "P006": ("male", 38), "P007": ("female", 45), "P008": ("male", 29),
    "P009": ("female", 36), "P010": ("male", 48),
}
V2_ORDER = [
    "patient_id", "interview_transcript", "to_review", "churn", "incomplete_journey",
    "gender", "age", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned",
    "biologic_type", "reasons_for_biologic_prescribed", "reasons_for_biologic_not_taken",
    "comorbid_conditions", "treatment_records", "treatment_outcome", "referral_pathway",
    "evidence_notes",
]
WRAP_COLS = {"interview_transcript", "treatment_records", "referral_pathway", "evidence_notes"}
NUMERIC_COLS = {"churn", "incomplete_journey", "biologic_prescribed", "biologic_taken", "biologic_not_mentioned"}

df = pd.read_excel(src_ods, engine="odf")
df = df.rename(columns={"reasons_for_biologic_denied": "reasons_for_biologic_not_taken"})
for col in ("gender", "age", "comorbid_conditions"):
    if col not in df.columns:
        df[col] = pd.NA
if "to_review" not in df.columns or not df["to_review"].notna().any():
    df["to_review"] = df["patient_id"].isin(VALIDATION_SEED).map({True: "TRUE", False: "FALSE"})
text_cols = [c for c in V2_ORDER if c not in NUMERIC_COLS and c != "patient_id"]
df[text_cols] = df[text_cols].astype("object")
for pid, chain in PATHWAYS.items():
    r = df["patient_id"] == pid
    df.loc[r & df["referral_pathway"].isna(), "referral_pathway"] = chain
for pid, (gender, age) in DEMOGRAPHICS.items():
    r = df["patient_id"] == pid
    df.loc[r & df["gender"].isna(), "gender"] = gender
    df.loc[r & df["age"].isna(), "age"] = age
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
