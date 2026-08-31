"""Core routing: resolve a request to an ordered candidate list."""
from __future__ import annotations

from dataclasses import dataclass

from .classifier import classify
from .config import RouterConfig
from .health import HealthRegistry


@dataclass
class RouteDecision:
    tier: str
    candidates: list[str]   # (provider, model) strings, fallback order
    skipped: list[tuple[str, str]]  # (candidate, reason)


class Router:
    def __init__(self, config: RouterConfig, health: HealthRegistry | None = None) -> None:
        self.config = config
        self.health = health or HealthRegistry(cooldown_s=config.cooldown_s)

    def resolve(self, prompt: str, requested_model: str = "auto") -> RouteDecision:
        """Build the fallback chain for a request.

        Explicit model requests pass through untouched (proxy mode).
        "auto" classifies the prompt and orders candidates: available
        providers first (registry order), cooling-down providers last
        as desperate fallbacks.
        """
        if requested_model != "auto":
            return RouteDecision(tier="explicit", candidates=[requested_model], skipped=[])

        tier = classify(prompt)
        rule = next((r for r in self.config.rules if r.tier == tier), None)
        if rule is None:
            return RouteDecision(tier=tier, candidates=[], skipped=[])

        candidates: list[str] = []
        skipped: list[tuple[str, str]] = []
        for cand in rule.candidates:
            provider = cand.split("/", 1)[0]
            if not self.health.get(provider).is_available():
                skipped.append((cand, "cooldown"))
                continue
            candidates.append(cand)

        # cooling-down providers still get tried last (better than failing)
        candidates.extend(c for c, _ in skipped)
        return RouteDecision(tier=tier, candidates=candidates, skipped=skipped)
