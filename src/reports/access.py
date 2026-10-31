"""Who may run which report and whose data they may see.

SRS REQ-44, NFR-SEC5 (server-side role checks) and NFR-SEC7 (no donor identity
for hospital users). This module only decides; it never reads the database.
"""

from django.core.exceptions import PermissionDenied

from accounts.models import Role

from .definitions import REPORTS

_ALL = frozenset(REPORTS)

# Deviation D-05 candidate: the SRS fixes only the hospital rule (REQ-44), so the
# role-to-report table below is a project decision.
ALLOWED_REPORTS = {
    Role.ADMIN: _ALL,
    Role.STAFF: _ALL,
    Role.HOSPITAL: frozenset({"request-issue"}),
}


def _slugs_for(user):
    return ALLOWED_REPORTS.get(getattr(user, "role", None), frozenset())


def can_run(user, slug):
    return slug in _slugs_for(user)


def allowed_reports(user):
    """The report definitions this user may see in the report list."""
    slugs = _slugs_for(user)
    return [spec for slug, spec in REPORTS.items() if slug in slugs]


def hospital_scope(user):
    """None for staff and admin (all data); the user's own hospital for a hospital user.

    The hospital always comes from the signed-in user, never from the request,
    so a hospital user cannot ask for another hospital's data.
    """
    if user.role != Role.HOSPITAL:
        return None
    hospital = getattr(user, "hospital", None)
    if hospital is None or not hospital.is_active:
        raise PermissionDenied
    return hospital
