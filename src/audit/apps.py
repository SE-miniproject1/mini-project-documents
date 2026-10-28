from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = "audit"

    def ready(self):
        from . import receivers  # noqa: F401  (connects the signal handlers)
