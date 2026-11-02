"""Expiry dates from component shelf life (SRS BR-4, REQ-16)."""

from datetime import timedelta

from django.conf import settings


def expiry_date_for(component_type, collection_date):
    days = settings.BBMS_SHELF_LIFE_DAYS[component_type]
    return collection_date + timedelta(days=days)
