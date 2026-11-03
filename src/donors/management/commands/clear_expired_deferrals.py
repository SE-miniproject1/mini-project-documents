from django.core.management.base import BaseCommand

from donors.services.deferrals import clear_expired_deferrals


class Command(BaseCommand):
    help = "Return donors to Eligible once their deferral review date has passed. Run nightly."

    def handle(self, *args, **options):
        cleared = clear_expired_deferrals()
        self.stdout.write(f"{cleared} donor(s) returned to Eligible.")
