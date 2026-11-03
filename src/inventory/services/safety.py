"""The screening rule, checked independently of unit status (SRS NFR-S1, BR-5).

A unit's status says it was released. This module answers the separate question of whether
the results on record would allow that release. Allocation and issue both ask it again, so a
unit whose status was changed by a script, a migration or a future bug still cannot go to a
patient without a complete, Non-Reactive panel.
"""

from collection.models import TestName, TestResult


def screening_root(unit):
    """The unit whose tests apply: a component is cleared by its whole blood parent."""
    return unit.parent_unit if unit.parent_unit_id else unit


def screening_problem(unit):
    """Why this unit may not go to a patient, or None if its panel is complete and clean."""
    root = screening_root(unit)
    results = dict(root.tests.values_list("test_name", "result"))
    missing = [name for name in TestName.values if name not in results]
    if missing:
        return "screening is incomplete (" + ", ".join(missing) + " not recorded)"
    reactive = [name for name, result in results.items() if result != TestResult.NON_REACTIVE]
    if reactive:
        return "screening is not clear (" + ", ".join(sorted(reactive)) + ")"
    return None
