import time

from django.core.management.base import BaseCommand

from notifications.dispatcher import dispatch_due


class Command(BaseCommand):
    help = "Send queued notifications, retrying failures. Use --loop to keep running as a worker."

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop", type=int, metavar="SECONDS", help="Check the queue every SECONDS."
        )

    def handle(self, *args, **options):
        while True:
            tried = dispatch_due()
            self.stdout.write(f"{tried} notification(s) tried.")
            if not options["loop"]:
                return
            time.sleep(options["loop"])
