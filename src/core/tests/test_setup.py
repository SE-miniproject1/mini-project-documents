import os
import subprocess
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

SRC = Path(__file__).resolve().parents[2]


class HealthTests(TestCase):
    def test_health_endpoint_reports_ok(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class SettingsTests(SimpleTestCase):
    """US-01: configuration comes from the environment and no secret is committed."""

    def _load(self, **env):
        base = {k: v for k, v in os.environ.items() if not k.startswith(("BBMS_", "DJANGO_"))}
        code = "import bbms.settings as s; print(s.SECRET_KEY != '', s.DEBUG, s.TIME_ZONE)"
        return subprocess.run(
            [sys.executable, "-c", code],
            cwd=SRC,
            env={**base, **env},
            capture_output=True,
            text=True,
        )

    def test_production_requires_a_secret_key(self):
        result = self._load(BBMS_ENV="production")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(ImproperlyConfigured.__name__, result.stderr)

    def test_production_accepts_a_secret_key_and_disables_debug(self):
        result = self._load(BBMS_ENV="production", DJANGO_SECRET_KEY="x" * 50)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["True", "False", "Asia/Kolkata"])

    def test_unknown_environment_is_rejected(self):
        self.assertNotEqual(self._load(BBMS_ENV="staging").returncode, 0)

    def test_no_secret_key_is_committed_in_settings(self):
        text = (SRC / "bbms" / "settings.py").read_text(encoding="utf-8")
        self.assertNotIn("django-insecure", text)
