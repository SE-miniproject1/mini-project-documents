from django.apps import AppConfig


class DonorsConfig(AppConfig):
    name = "donors"

    def ready(self):
        from . import checks  # noqa: F401  (registers the system checks)
