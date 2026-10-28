from django.core.management.base import BaseCommand

from inventory.services.expiry import expire_due_units, send_expiry_digest


class Command(BaseCommand):
    help = (
        "Mark units past their expiry date as Expired and email the near-expiry digest. Run daily."
    )

    def add_arguments(self, parser):
        parser.add_argument("--no-digest", action="store_true", help="Skip the digest email.")

    def handle(self, *args, **options):
        expired = expire_due_units()
        self.stdout.write(f"{expired} unit(s) marked Expired.")
        if not options["no_digest"]:
            sent = send_expiry_digest()
            self.stdout.write("Near-expiry digest sent." if sent else "No digest needed.")
