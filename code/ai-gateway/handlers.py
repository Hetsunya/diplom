import asyncio
from pathlib import Path
import pkgutil
from importlib import import_module
from typing import Any, Awaitable, Callable, Protocol


class Plugin(Protocol):
    name: str

    def can_handle(self, msg: dict[str, Any]) -> bool: ...

    async def process(self, msg: dict[str, Any]) -> None: ...


def _load_plugins() -> list[Plugin]:
    """
    Auto-discover modules in `plugins/*` and collect plugin instances.

    A new plugin should be added as a single file into `plugins/`.
    """
    plugins: list[Plugin] = []

    package = "plugins"
    plugins_dir = Path(__file__).resolve().parent / "plugins"
    for mod in pkgutil.iter_modules([str(plugins_dir)]):
        module_name = f"{package}.{mod.name}"
        imported = import_module(module_name)

        instance = getattr(imported, "plugin", None)
        if instance is not None:
            plugins.append(instance)

    return plugins


_PLUGINS: list[Plugin] = []


def _get_plugins() -> list[Plugin]:
    global _PLUGINS
    if not _PLUGINS:
        _PLUGINS = _load_plugins()
    return _PLUGINS


async def handle_message(msg: dict[str, Any]):
    for plugin in _get_plugins():
        if plugin.can_handle(msg):
            await plugin.process(msg)
            return

    # Fallback for messages without matching plugin.
    print("[WS] message:", msg)
