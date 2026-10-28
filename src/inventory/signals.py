from django.dispatch import Signal

# Sent inside the same database transaction as every unit status change (SRS REQ-23).
# Receivers get: unit, previous, new, by (the acting user or None) and reason.
# A receiver that raises rolls the status change back, so a transition can never be
# recorded without its audit entry.
unit_status_changed = Signal()
