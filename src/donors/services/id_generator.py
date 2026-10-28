"""Donor identifiers: `DNR` followed by eight digits (SRS REQ-2)."""

import re

from core.models import IdSequence

DONOR_ID_PATTERN = re.compile(r"^DNR\d{8}$")
SEQUENCE = "donor"
FIRST_NUMBER = 10000001


def generate_donor_id():
    return f"DNR{IdSequence.next_value(SEQUENCE, FIRST_NUMBER)}"
