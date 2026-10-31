"""Report export (SRS REQ-43, NFR-Q8). Works on a ReportResult, needs no database."""

import csv
import io

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
