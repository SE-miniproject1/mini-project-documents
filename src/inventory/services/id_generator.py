"""Unit identifiers: `BU` followed by ten digits (SRS REQ-10)."""

import re

from core.models import IdSequence

UNIT_ID_PATTERN = re.compile(r"^BU\d{10}$")
SEQUENCE = "unit"
FIRST_NUMBER = 1000000001


def generate_unit_id():
    return f"BU{IdSequence.next_value(SEQUENCE, FIRST_NUMBER)}"
