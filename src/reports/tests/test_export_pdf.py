from datetime import date, datetime

from django.test import SimpleTestCase

from reports.services.export import to_pdf
from reports.services.result import ReportResult


def sample_result(rows=(("O-", "PRBC", 8), ("A+", "PRBC", 12))):
    return ReportResult(
        title="Inventory Status Report",
        columns=("Blood Group", "Component Type", "Available Count"),
        rows=rows,
        start=date(2026, 9, 1),
        end=date(2026, 9, 30),
        generated_by="staff01",
        generated_at=datetime(2026, 10, 31, 18, 30, 5),
    )


class PdfExportTests(SimpleTestCase):
    """UT-45 (PDF): a legible PDF that carries the provenance header."""

    def test_output_is_a_pdf(self):
        self.assertTrue(to_pdf(sample_result()).startswith(b"%PDF"))

    def test_header_carries_name_range_user_and_timestamp(self):
        data = to_pdf(sample_result(), compress=False)
        for expected in (
            b"Inventory Status Report",
            b"01-09-2026 to 30-09-2026",
            b"staff01",
            b"31-10-2026 18:30:05",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, data)

    def test_markup_characters_in_data_do_not_break_the_pdf(self):
        data = to_pdf(sample_result(rows=(("Apollo & <Sons>", "PRBC", 1),)))
        self.assertTrue(data.startswith(b"%PDF"))

    def test_empty_report_still_exports(self):
        data = to_pdf(sample_result(rows=()), compress=False)
        self.assertIn(b"No records in the selected date range.", data)

    def test_long_report_spans_several_pages(self):
        rows = tuple(("O-", "PRBC", n) for n in range(400))
        data = to_pdf(sample_result(rows=rows), compress=False)
        self.assertIn(b"Page 2", data)
