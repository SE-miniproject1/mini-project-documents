from django.apps import AppConfig


class BloodRequestsConfig(AppConfig):
    name = "bloodrequests"
    label = "bloodrequests"

    def ready(self):
        from . import receivers  # noqa: F401
