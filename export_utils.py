from __future__ import annotations

from io import BytesIO

import pandas as pd
from fpdf import FPDF


def export_dataframe_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return output.getvalue()


def export_pdf_report(title: str, summary_lines: list[str], table: pd.DataFrame | None = None) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    usable_width = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(usable_width, 10, safe_pdf_text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    for line in summary_lines:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(usable_width, 7, safe_pdf_text(line), new_x="LMARGIN", new_y="NEXT")
    if table is not None and not table.empty:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(usable_width, 6, "Table", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=8)
        clean_table = table.copy()
        clean_table.columns = [safe_pdf_text(column) for column in clean_table.columns]
        for row in clean_table.head(25).astype(str).itertuples(index=False):
            line = safe_pdf_text(" | ".join(row))
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(usable_width, 5, line[:220], new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output(dest="S"))


def safe_pdf_text(value) -> str:
    replacements = {"₹": "Rs", "–": "-", "—": "-", "→": "->", "⚠": "Warning"}
    text = str(value)
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("latin-1", "ignore").decode("latin-1")
