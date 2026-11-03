from django.test import SimpleTestCase

from reports.definitions import REPORTS


class ReportDefinitionTests(SimpleTestCase):
    """REQ-42: six reports, each with the ten Appendix B.7 columns."""

    def test_six_reports_are_defined(self):
        self.assertEqual(len(REPORTS), 6)

    def test_each_report_has_ten_unique_columns(self):
        for spec in REPORTS.values():
            with self.subTest(report=spec.slug):
                self.assertEqual(len(spec.columns), 10)
                self.assertEqual(len(set(spec.columns)), 10)
