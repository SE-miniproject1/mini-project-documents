"""Administrator-configurable parameters (SRS REQ-46, NFR-Q10).

Each parameter has a built-in default in settings and an optional override stored in the
database. Callers ask this module, never settings directly, so a change made on the
configuration screen applies to the next request with no restart.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction

from .models import ConfigValue

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
COMPONENTS = ("Whole Blood", "PRBC", "FFP", "Platelets", "Cryoprecipitate")


@dataclass(frozen=True)
class Param:
    key: str
    label: str
    kind: type  # int or Decimal
    low: int
    high: int
    section: str
    help: str = ""


def _elig(key, label, kind, low, high, help=""):
    return Param(f"eligibility.{key}", label, kind, low, high, "Donor eligibility", help)


PARAMS = (
    _elig("min_age", "Minimum donor age (years)", int, 16, 25),
    _elig("max_age", "Maximum donor age (years)", int, 40, 100),
    _elig("min_weight_kg", "Minimum weight (kg)", Decimal, 30, 120),
    _elig("min_haemoglobin", "Minimum haemoglobin (g/dL)", Decimal, 5, 20),
    _elig("min_systolic", "Minimum systolic pressure (mmHg)", int, 70, 130),
    _elig("max_systolic", "Maximum systolic pressure (mmHg)", int, 120, 220),
    _elig(
        "donation_interval_days",
        "Minimum days between whole blood donations",
        int,
        90,
        365,
        "Cannot be set below 90 days (BR-2).",
    ),
    _elig(
        "deferral_review_days", "Days before a physical-criteria deferral is reviewed", int, 1, 365
    ),
    Param(
        "near_expiry_days",
        "Near-expiry window (days)",
        int,
        1,
        30,
        "Stock",
        "Units this close to expiry are flagged and listed in the daily digest.",
    ),
    *(
        Param(f"shelf_life.{c}", f"{c} shelf life (days)", int, 1, 1000, "Shelf life")
        for c in COMPONENTS
    ),
    *(
        Param(
            f"min_stock.{g}",
            f"Minimum stock, {g} (units)",
            int,
            0,
            10000,
            "Minimum stock",
            "0 means no threshold.",
        )
        for g in BLOOD_GROUPS
    ),
)
BY_KEY = {p.key: p for p in PARAMS}


def _default(key):
    scope, _, name = key.partition(".")
    if scope == "eligibility":
        return settings.BBMS_ELIGIBILITY[name]
    if scope == "shelf_life":
        return settings.BBMS_SHELF_LIFE_DAYS[name]
    if scope == "min_stock":
        return getattr(settings, "BBMS_MIN_STOCK", {}).get(name, 0)
    return settings.BBMS_NEAR_EXPIRY_DAYS


def _parse(param, text):
    try:
        return param.kind(text)
    except (InvalidOperation, ValueError):
        return None


def overrides():
    return {row.key: row.value for row in ConfigValue.objects.all()}


def current_values():
    """Every parameter's effective value, as {key: value}."""
    stored = overrides()
    values = {}
    for param in PARAMS:
        parsed = _parse(param, stored[param.key]) if param.key in stored else None
        values[param.key] = parsed if parsed is not None else _default(param.key)
    return values


def eligibility_rules():
    rules = dict(settings.BBMS_ELIGIBILITY)
    for key, value in current_values().items():
        scope, _, name = key.partition(".")
        if scope == "eligibility":
            rules[name] = value
    return rules


def near_expiry_days():
    return current_values()["near_expiry_days"]


def shelf_life_days(component):
    return current_values()[f"shelf_life.{component}"]


def min_stock(group):
    return current_values()[f"min_stock.{group}"]


def validate(values):
    """Return {key: message} for anything out of range or inconsistent. Empty means valid."""
    problems = {}
    for key, value in values.items():
        param = BY_KEY[key]
        if value < param.low or value > param.high:
            problems[key] = f"Enter a value from {param.low} to {param.high}."
    elig = {k.split(".", 1)[1]: v for k, v in values.items() if k.startswith("eligibility.")}
    if (
        "min_systolic" in elig
        and "max_systolic" in elig
        and elig["min_systolic"] >= elig["max_systolic"]
    ):
        problems.setdefault("eligibility.max_systolic", "Must be above the minimum pressure.")
    return problems


@transaction.atomic
def save(values, *, by):
    """Store `values` (already validated), auditing each change. Returns the changed keys."""
    from audit.models import Event
    from audit.services import record_event

    before = current_values()
    changed = []
    for key, value in values.items():
        if before[key] == value:
            continue
        ConfigValue.objects.update_or_create(
            key=key, defaults={"value": str(value), "updated_by": by}
        )
        record_event(
            Event.CONFIG_CHANGE,
            actor=by,
            entity_type="Config",
            entity_id=key,
            previous=before[key],
            new=value,
        )
        changed.append(key)
    return changed
