from django.template import Context, Template
from django.test import RequestFactory, TestCase

from accounts.models import User
from core.listing import PAGE_SIZE, SortState, apply_sort, paginate

ALLOWED = {"name": "username", "email": "email"}


class ListingTests(TestCase):
    """US-03 (SRS UI-2): 25 rows per page and sortable columns."""

    @classmethod
    def setUpTestData(cls):
        for number in range(60):
            User.objects.create_user(f"user{number:02d}", f"u{number:02d}@example.com", "x")

    def _request(self, query=""):
        return RequestFactory().get(f"/list/{query}")

    def test_the_page_size_is_twenty_five(self):
        self.assertEqual(PAGE_SIZE, 25)
        page = paginate(self._request(), User.objects.order_by("pk"))
        self.assertEqual(len(page.object_list), 25)
        self.assertEqual(page.paginator.num_pages, 3)

    def test_later_pages_and_the_last_partial_page(self):
        self.assertEqual(len(paginate(self._request("?page=3"), User.objects.order_by("pk"))), 10)

    def test_bad_page_numbers_return_a_valid_page(self):
        self.assertEqual(
            paginate(self._request("?page=abc"), User.objects.order_by("pk")).number, 1
        )
        self.assertEqual(
            paginate(self._request("?page=999"), User.objects.order_by("pk")).number, 3
        )

    def test_sort_ascending_by_default(self):
        qs, state = apply_sort(self._request(), User.objects.order_by("pk"), ALLOWED, "name")
        self.assertEqual(state, SortState("name", "asc"))
        self.assertEqual(qs.first().username, "user00")

    def test_sort_descending_on_request(self):
        qs, state = apply_sort(
            self._request("?sort=name&dir=desc"), User.objects.order_by("pk"), ALLOWED, "name"
        )
        self.assertEqual(state.direction, "desc")
        self.assertEqual(qs.first().username, "user59")

    def test_a_field_that_was_not_offered_cannot_be_sorted_on(self):
        _, state = apply_sort(
            self._request("?sort=password"), User.objects.order_by("pk"), ALLOWED, "name"
        )
        self.assertEqual(state.key, "name")

    def test_sort_header_links_reverse_the_active_column_and_reset_the_page(self):
        request = self._request("?sort=name&dir=asc&page=2&q=x")
        html = Template('{% load bbms_ui %}{% sort_header state "name" "Name" %}').render(
            Context({"request": request, "state": SortState("name", "asc")})
        )
        self.assertIn('aria-sort="ascending"', html)
        self.assertIn("dir=desc", html)
        self.assertIn("q=x", html)
        self.assertNotIn("page=", html)

    def test_inactive_columns_start_ascending(self):
        html = Template('{% load bbms_ui %}{% sort_header state "email" "Email" %}').render(
            Context({"request": self._request(), "state": SortState("name", "asc")})
        )
        self.assertIn('aria-sort="none"', html)
        self.assertIn("sort=email", html)
        self.assertIn("dir=asc", html)
