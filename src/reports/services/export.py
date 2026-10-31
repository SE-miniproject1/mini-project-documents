"""Report export (SRS REQ-43, NFR-Q8). Works on a ReportResult, needs no database."""

import csv
import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .result import format_value

# A cell starting with one of these can run as a formula in Excel (CSV injection).
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe(value):
    text = format_value(value)
    if isinstance(value, str) and text.startswith(_FORMULA_PREFIXES):
        return "'" + text
    return text


def to_csv(result):
    """Return the report as RFC 4180 CSV bytes.

    RFC 4180 wants the same number of fields on every line, so the provenance
    lines and the blank separator are padded to the width of the table.
    """
    width = len(result.columns)
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    for label, value in result.provenance:
        cells = [label, _safe(value)]
        writer.writerow(cells + [""] * (width - len(cells)))
    writer.writerow([""] * width)
    writer.writerow(result.columns)
    for row in result.rows:
        writer.writerow([_safe(cell) for cell in row])
    return buffer.getvalue().encode("utf-8")


_MARGIN = 24
_CELL = ParagraphStyle("cell", fontName="Helvetica", fontSize=7, leading=8.5)
_HEAD = ParagraphStyle("head", parent=_CELL, fontName="Helvetica-Bold")


def _paragraph(value, style):
    # Paragraph reads its text as markup, so & and < in data must be escaped.
    return Paragraph(escape(format_value(value)), style)


def to_pdf(result, compress=True):
    """Return the report as PDF bytes, with the provenance header on page 1.

    `compress=False` leaves page text readable in the raw bytes, for tests.
    """
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_MARGIN,
        bottomMargin=_MARGIN + 10,
        title=result.title,
        author=result.generated_by,
        pageCompression=1 if compress else 0,
    )
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(result.title), styles["Title"])]
    for label, value in result.provenance[1:]:
        story.append(Paragraph(f"<b>{escape(label)}:</b> {escape(value)}", styles["Normal"]))
    story.append(Spacer(1, 10))

    if result.rows:
        table_rows = [[_paragraph(name, _HEAD) for name in result.columns]]
        table_rows += [[_paragraph(cell, _CELL) for cell in row] for row in result.rows]
        table = Table(table_rows, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No records in the selected date range.", styles["Normal"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(_MARGIN, 14, f"{result.title}  |  Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
