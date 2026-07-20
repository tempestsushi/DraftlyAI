from __future__ import annotations

import warnings
from functools import wraps

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
    from langchain_core.load.load import Reviver
except ImportError:  # pragma: no cover - optional dependency edge
    LangChainPendingDeprecationWarning = PendingDeprecationWarning
    Reviver = None


def configure_langchain_defaults() -> None:
    if Reviver is None or getattr(Reviver.__init__, "_draftly_patched", False):
        return

    original_init = Reviver.__init__

    @wraps(original_init)
    def patched_init(self, allowed_objects=None, *args, **kwargs):
        if allowed_objects is None:
            allowed_objects = "messages"
        original_init(self, allowed_objects, *args, **kwargs)

    patched_init._draftly_patched = True  # type: ignore[attr-defined]
    Reviver.__init__ = patched_init


def configure_warning_filters() -> None:
    warnings.filterwarnings(
        "ignore",
        message=r"You are using a Python version .* which Google will stop supporting.*",
        category=FutureWarning,
        module=r"google\.api_core\._python_version_support",
    )
    warnings.filterwarnings(
        "ignore",
        message=r"The default value of `allowed_objects` will change in a future version\..*",
        category=LangChainPendingDeprecationWarning,
    )
    warnings.simplefilter("ignore", LangChainPendingDeprecationWarning)
    configure_langchain_defaults()
