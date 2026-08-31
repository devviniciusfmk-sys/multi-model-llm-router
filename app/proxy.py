"""OpenAI-compatible passthrough to the chosen provider."""
from __future__ import annotations

import os
import time

import httpx


class ProviderError(Exception):
    def __init__(self, provider: str, status: int, detail: str) -> None:
        self.provider = provider
        self.status = status
        super().__init__(f"{provider} returned {status}: {detail}")


def api_key_for(provider_cfg) -> str:
    key = os.environ.get(provider_cfg.api_key_env, "")
    if not key:
        raise ProviderError(provider_cfg.name, 401, f"missing env {provider_cfg.api_key_env}")
    return key


async def forward(provider_cfg, model: str, payload: dict) -> dict:
    """Forward a chat-completions payload; raises ProviderError on failure."""
    url = f"{provider_cfg.base_url.rstrip('/')}/chat/completions"
    body = {**payload, "model": model}
    headers = {"Authorization": f"Bearer {api_key_for(provider_cfg)}"}
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=provider_cfg.timeout_s) as client:
        resp = await client.post(url, json=body, headers=headers)
    latency_ms = (time.monotonic() - start) * 1000
    if resp.status_code >= 400:
        raise ProviderError(provider_cfg.name, resp.status_code, resp.text[:300])
    data = resp.json()
    data["_meta"] = {"provider": provider_cfg.name, "model": model, "latency_ms": round(latency_ms, 1)}
    return data
