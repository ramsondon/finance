# Loads base settings, then optionally overrides from settings_local.py
from .settings_base import *  # noqa

try:
    from .settings_local import *  # type: ignore # noqa
except Exception:
    pass

