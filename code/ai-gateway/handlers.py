from typing import Any, Protocol


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


def _get_plugins() -> list[Plugin]:
    global _PLUGINS
    if not _PLUGINS:
        _PLUGINS = _load_plugins()
    return _PLUGINS


def _plugin_sort_key(p: Plugin) -> int:
    return int(getattr(p, "priority", 500))


async def handle_message(msg: dict[str, Any], ws: Any) -> None:
    """Dispatch to all plugins that can handle the message (sorted by priority)."""
    for plugin in sorted(_get_plugins(), key=_plugin_sort_key):
        if plugin.can_handle(msg):
            await plugin.process(msg, ws)
