"""Load modular AI gateway configuration (JSON)."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModuleCfg:
    enabled: bool = True
    provider: str = ""
    model: str = ""
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class GatewayConfig:
    modules: dict[str, ModuleCfg] = field(default_factory=dict)

    def module(self, name: str) -> ModuleCfg | None:
        return self.modules.get(name)


def _default_config_path() -> Path:
    return Path(__file__).resolve().parent / "modules.default.json"


def load_gateway_config() -> GatewayConfig:
    path = os.getenv("AI_GATEWAY_MODULES_CONFIG", "")
    if path and Path(path).is_file():
        raw = Path(path).read_text(encoding="utf-8")
    else:
        raw = _default_config_path().read_text(encoding="utf-8")
    data = json.loads(raw)
    modules_raw = data.get("modules") or {}
    modules: dict[str, ModuleCfg] = {}
    for key, val in modules_raw.items():
        if not isinstance(val, dict):
            continue
        modules[key] = ModuleCfg(
            enabled=bool(val.get("enabled", True)),
            provider=str(val.get("provider", "")),
            model=str(val.get("model", "")),
            params=dict(val.get("params") or {}),
        )
    return GatewayConfig(modules=modules)


_CFG: GatewayConfig | None = None


def get_gateway_config() -> GatewayConfig:
    global _CFG
    if _CFG is None:
        _CFG = load_gateway_config()
    return _CFG


def set_gateway_config(cfg: GatewayConfig) -> None:
    global _CFG
    _CFG = cfg


def config_snapshot() -> dict[str, Any]:
    """JSON-serializable snapshot for report metadata."""
    cfg = get_gateway_config()
    snap: dict[str, Any] = {"modules": {}}
    for name, m in cfg.modules.items():
        snap["modules"][name] = {
            "enabled": m.enabled,
            "provider": m.provider,
            "model": m.model,
            "params": deepcopy(m.params),
        }
    return snap
