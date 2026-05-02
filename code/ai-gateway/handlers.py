import os
import time
from typing import Any, Protocol

from observability import log_event


class Plugin(Protocol):
    name: str

    def can_handle(self, msg: dict[str, Any]) -> bool: ...

    async def process(self, msg: dict[str, Any], ws: Any) -> None: ...


def _load_plugins() -> list[Plugin]:
    """
    Load analyzers from `modules/` (see `modules/registry.py`).

    Legacy `plugins/*` files are thin shims for compatibility only.
    """
    from modules.registry import iter_plugins

    return list(iter_plugins())


_PLUGINS: list[Plugin] = []
_LAST_CFG_POLL_MONO: float = 0.0


def _get_plugins() -> list[Plugin]:
    global _PLUGINS
    if not _PLUGINS:
        _PLUGINS = _load_plugins()
    return _PLUGINS


def _plugin_sort_key(p: Plugin) -> int:
    return int(getattr(p, "priority", 500))


async def handle_message(msg: dict[str, Any], ws: Any) -> None:
    """Dispatch to all plugins that can handle the message (sorted by priority)."""
    global _LAST_CFG_POLL_MONO
    poll = float(os.getenv("AI_GATEWAY_CONFIG_POLL_SEC", "10"))
    if poll > 0:
        now = time.monotonic()
        if now - _LAST_CFG_POLL_MONO >= poll:
            _LAST_CFG_POLL_MONO = now
            from gateway_config import maybe_reload_gateway_config

            if maybe_reload_gateway_config():
                log_event("gateway_config_reloaded")

    for plugin in sorted(_get_plugins(), key=_plugin_sort_key):
        if plugin.can_handle(msg):
            await plugin.process(msg, ws)
