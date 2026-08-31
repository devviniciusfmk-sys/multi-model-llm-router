"""Provider health tracking with cooldown and background probes."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class ProviderHealth:
    name: str
    cooldown_until: float = 0.0
    consecutive_failures: int = 0
    last_latency_ms: float | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def is_available(self, now: float | None = None) -> bool:
        return (now or time.monotonic()) >= self.cooldown_until

    def record_failure(self, cooldown_s: int, now: float | None = None) -> None:
        with self._lock:
            now = now or time.monotonic()
            self.consecutive_failures += 1
            # exponential-ish backoff, capped at 8x
            factor = min(2 ** max(0, self.consecutive_failures - 1), 8)
            self.cooldown_until = now + cooldown_s * factor

    def record_success(self, latency_ms: float, now: float | None = None) -> None:
        with self._lock:
            self.consecutive_failures = 0
            self.cooldown_until = 0.0
            self.last_latency_ms = latency_ms


class HealthRegistry:
    def __init__(self, cooldown_s: int = 120) -> None:
        self.cooldown_s = cooldown_s
        self._health: dict[str, ProviderHealth] = {}

    def get(self, provider: str) -> ProviderHealth:
        if provider not in self._health:
            self._health[provider] = ProviderHealth(name=provider)
        return self._health[provider]

    def available_providers(self) -> list[str]:
        return [n for n, h in self._health.items() if h.is_available()]

    def record_failure(self, provider: str) -> None:
        self.get(provider).record_failure(self.cooldown_s)

    def record_success(self, provider: str, latency_ms: float) -> None:
        self.get(provider).record_success(latency_ms)
