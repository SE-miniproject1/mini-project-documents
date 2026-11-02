"""Expiry dates from component shelf life (SRS BR-4, REQ-16)."""

from datetime import timedelta

from core import config


def expiry_date_for(component_type, collection_date):
    days = config.shelf_life_days(component_type)
    return collection_date + timedelta(days=days)
