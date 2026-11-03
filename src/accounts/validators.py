"""Password rules beyond Django's built-ins (SRS NFR-SEC3)."""

import re

from django.core.exceptions import ValidationError


class ComplexityValidator:
    """Require at least one letter, one digit and one special character."""

    def validate(self, password, user=None):
        problems = []
        if not re.search(r"[A-Za-z]", password):
            problems.append("a letter")
        if not re.search(r"\d", password):
            problems.append("a digit")
        if not re.search(r"[^A-Za-z0-9]", password):
            problems.append("a special character")
        if problems:
            raise ValidationError(
                "Password must contain " + ", ".join(problems) + ".",
                code="password_too_simple",
            )

    def get_help_text(self):
        return "Your password must contain a letter, a digit and a special character."
