from django.core.management.base import BaseCommand

from notifications.tasks.reminders import queue_camp_reminders, queue_eligibility_reminders
from notifications.tasks.shortage import queue_shortage_appeals


class Command(BaseCommand):
    help = (
        "Queue eligibility and camp reminders and shortage appeals. Run hourly; "
        "dispatch_notifications sends them."
    )

    def handle(self, *args, **options):
        self.stdout.write(f"{queue_eligibility_reminders()} eligibility reminder(s) queued.")
        self.stdout.write(f"{queue_camp_reminders()} camp reminder(s) queued.")
        for group, count in queue_shortage_appeals().items():
            self.stdout.write(f"{group} is below its minimum: {count} appeal(s) queued.")
