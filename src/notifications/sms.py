"""SMS gateway backends (SRS SI-4).

The dispatcher calls `get_backend().send(number, text)`. A backend returns the gateway's
delivery status as a short string and raises `SMSError` when the message was not accepted.
`BBMS_SMS_BACKEND` names the class to use.
"""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class SMSError(Exception):
    pass


class ConsoleBackend:
    """Development: log the message instead of sending it."""

    def send(self, number, text):
        logger.info("sms to=%s text=%s", number, text)
        return "logged"


class LocmemBackend:
    """Tests: keep messages in `outbox`, like Django's locmem email backend."""

    outbox = []

    def send(self, number, text):
        LocmemBackend.outbox.append((number, text))
        return "accepted"


class HttpBackend:
    """Production: POST to the gateway over HTTPS with a bearer token."""

    def send(self, number, text):
        url = settings.BBMS_SMS_URL
        if not url.startswith("https://"):
            raise SMSError("The SMS gateway URL must use HTTPS.")
        request = urllib.request.Request(
            url,
            data=json.dumps({"to": number, "message": text}).encode(),
            headers={
                "Authorization": f"Bearer {settings.BBMS_SMS_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
                reply = json.loads(response.read() or b"{}")
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise SMSError(str(exc)) from exc
        return str(reply.get("status", "accepted"))[:60]


def get_backend():
    return import_string(settings.BBMS_SMS_BACKEND)()
