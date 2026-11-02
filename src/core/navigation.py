"""Role-scoped navigation (SRS UI-1, UI-6).

The registry lists every screen in the SRS screen inventory with the roles that
may see it. A link only appears once its URL exists, so each story can add its
page and the menu picks it up without touching this file.
"""

from dataclasses import dataclass

from django.urls import NoReverseMatch, reverse

from accounts.models import Role

EVERYONE = tuple(Role.values)
STAFF_SIDE = (Role.STAFF, Role.ADMIN)


@dataclass(frozen=True)
class NavItem:
    label: str
    url_name: str
    roles: tuple


NAV_ITEMS = (
    NavItem("Home", "home", EVERYONE),
    # Donor
    NavItem("My eligibility", "donors:dashboard", (Role.DONOR,)),
    NavItem("Upcoming camps", "camps:list", (Role.DONOR,)),
    # Blood bank staff and administrators
    NavItem("Donor search and screening", "donors:search", STAFF_SIDE),
    NavItem("Inventory", "inventory:console", STAFF_SIDE),
    NavItem("Request queue", "requests:queue", (Role.STAFF,)),
    NavItem("Camp management", "camps:manage", STAFF_SIDE),
    # Hospital
    NavItem("Raise a request", "requests:new", (Role.HOSPITAL,)),
    NavItem("My requests", "requests:tracker", (Role.HOSPITAL,)),
    NavItem("Check availability", "search:availability", (Role.HOSPITAL,)),
    # Reports and administration
    NavItem("Reports", "reports:index", (Role.STAFF, Role.HOSPITAL, Role.ADMIN)),
    NavItem("Users and roles", "accounts:user_admin", (Role.ADMIN,)),
    NavItem("Configuration", "config:settings", (Role.ADMIN,)),
)


def nav_for(user):
    """Return (label, url, url_name) for each link this user may see and that exists."""
    if not user.is_authenticated:
        return []
    links = []
    for item in NAV_ITEMS:
        if user.role not in item.roles:
            continue
        try:
            url = reverse(item.url_name)
        except NoReverseMatch:
            continue
        links.append({"label": item.label, "url": url, "url_name": item.url_name})
    return links
