"""Stock counts for the inventory console (SRS REQ-17, NFR-P5, NFR-S2).

Everything is read from the database on each request, never cached, so a change
committed by one user is visible to the next request from anyone.
"""

from dataclasses import dataclass
from datetime import date

from django.db.models import Count

from donors.models import BloodGroup
from inventory.models import BloodUnit, Component, Status

GROUPS = tuple(BloodGroup.values)
COMPONENTS = tuple(Component.values)


@dataclass(frozen=True)
class StockGrid:
    groups: tuple
    components: tuple
    cells: dict  # {(blood_group, component): count}
    row_totals: dict
    column_totals: dict
    total: int

    def rows(self):
        """For templates: (blood group, [counts in component order], row total)."""
        for group in self.groups:
            counts = [self.cells.get((group, component), 0) for component in self.components]
            yield group, counts, self.row_totals.get(group, 0)


def stock_grid(today=None):
    """Available units by blood group and component. Only issuable units count (REQ-11)."""
    counted = (
        BloodUnit.objects.issuable(today or date.today())
        .values("blood_group", "component_type")
        .annotate(n=Count("id"))
    )
    cells = {(row["blood_group"], row["component_type"]): row["n"] for row in counted}
    row_totals = {g: sum(cells.get((g, c), 0) for c in COMPONENTS) for g in GROUPS}
    column_totals = {c: sum(cells.get((g, c), 0) for g in GROUPS) for c in COMPONENTS}
    return StockGrid(
        GROUPS, COMPONENTS, cells, row_totals, column_totals, sum(row_totals.values())
    )


def status_counts():
    """How many units are in each status, including statuses with none."""
    found = dict(BloodUnit.objects.values_list("status").annotate(n=Count("id")))
    return {status.value: found.get(status.value, 0) for status in Status}
