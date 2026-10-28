"""Remembers the current request so an entry can name the source address (NFR-SEC10)."""

import contextvars

_current = contextvars.ContextVar("audit_request", default=None)


def set_request(request):
    return _current.set(request)


def reset(token):
    _current.reset(token)


def current_request():
    return _current.get()
