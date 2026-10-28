"""WSGI entry point (served by Gunicorn behind Nginx, SRS OE-2)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bbms.settings")
application = get_wsgi_application()
