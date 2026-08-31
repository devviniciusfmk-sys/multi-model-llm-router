"""Provider registry loaded from YAML config."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    name: str
    base_url: str
    api_key_env: str
    models: list[str] = Field(default_factory=list)
    cost_tier: int = 1          # 0 = free/cheap, 3 = premium
    timeout_s: float = 60.0


class RoutingRule(BaseModel):
    """Maps a task tier to an ordered list of (provider, model) candidates."""
    tier: str
    candidates: list[str]       # e.g. ["groq/llama-70b", "openai/gpt-4o-mini"]


class RouterConfig(BaseModel):
    providers: dict[str, ProviderConfig]
    rules: list[RoutingRule]
    cooldown_s: int = 120
    max_fallbacks: int = 3


DEFAULT_TIERS = ["reasoning", "code", "writing", "bulk"]


@lru_cache
def load_config(path: str | None = None) -> RouterConfig:
    cfg_path = Path(path or os.environ.get("ROUTER_CONFIG", "config/routers.yaml"))
    raw = yaml.safe_load(cfg_path.read_text())
    return RouterConfig.model_validate(raw)
