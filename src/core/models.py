from django.db import models, transaction
from django.db.models import F


class IdSequence(models.Model):
    """A named counter used to hand out unique, never-reused identifiers.

    Donor IDs (SRS REQ-2) and unit IDs (REQ-10) come from here. The increment is a
    single UPDATE, so two simultaneous requests cannot receive the same number, and
    it commits or rolls back with the transaction that uses the number, so a failed
    registration leaves no gap.
    """

    name = models.CharField(max_length=40, unique=True)
    last_value = models.BigIntegerField(default=0)

    @classmethod
    def next_value(cls, name, start):
        """Return the next number for `name`, beginning at `start`."""
        with transaction.atomic():
            cls.objects.get_or_create(name=name, defaults={"last_value": start - 1})
            cls.objects.filter(name=name).update(last_value=F("last_value") + 1)
            return cls.objects.values_list("last_value", flat=True).get(name=name)
