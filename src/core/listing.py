"""Sorting and pagination for list screens (SRS UI-2: 25 rows per page, sortable columns)."""

from dataclasses import dataclass

from django.core.paginator import Paginator

PAGE_SIZE = 25


@dataclass(frozen=True)
class SortState:
    key: str
    direction: str  # "asc" or "desc"


def apply_sort(request, queryset, allowed, default):
    """Order a queryset by ?sort=<key>&dir=<asc|desc>.

    `allowed` maps public keys to ORM fields, so a request can never order by a
    field the view did not offer. Unknown keys fall back to `default`.
    """
    key = request.GET.get("sort")
    if key not in allowed:
        key = default
    direction = "desc" if request.GET.get("dir") == "desc" else "asc"
    field = allowed[key]
    ordering = f"-{field}" if direction == "desc" else field
    return queryset.order_by(ordering, "pk"), SortState(key, direction)


def paginate(request, items, per_page=PAGE_SIZE):
    """Return the requested page. Bad or out-of-range page numbers give a valid page."""
    return Paginator(items, per_page).get_page(request.GET.get("page"))
