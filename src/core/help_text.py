"""Context-sensitive help (SRS UI-2). Keyed by URL name, with a general fallback."""

GENERAL = (
    "Use the menu on the left to move between screens. Fields marked required must be filled in. "
    "If something is wrong, a message beside the field and a summary at the top of the form "
    "say what to correct."
)

TOPICS = {
    "home": "This page lists the screens you can use. Pick one from the menu or the cards below.",
    "accounts:login": (
        "Sign in with your username and password. After 5 wrong attempts the account is locked "
        "for 15 minutes."
    ),
    "accounts:password_change": (
        "Choose a password of at least 10 characters with a letter, a digit and a special "
        "character. Changing it signs you out of every other session."
    ),
}


def help_for(url_name):
    return TOPICS.get(url_name, GENERAL)
