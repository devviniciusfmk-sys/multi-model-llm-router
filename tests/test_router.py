from app.config import ProviderConfig, RoutingRule, RouterConfig
from app.health import HealthRegistry
from app.router import Router


def make_router(cooling_down: set[str] | None = None) -> Router:
    cfg = RouterConfig(
        providers={
            "openrouter": ProviderConfig(
                name="openrouter", base_url="https://x/v1",
                api_key_env="K", cost_tier=1,
            )
        },
        rules=[
            RoutingRule(tier="code", candidates=[
                "openrouter/anthropic/claude-3.5-sonnet",
                "openrouter/openai/gpt-4o-mini",
            ]),
        ],
        cooldown_s=120,
    )
    health = HealthRegistry(cooldown_s=120)
    for p in cooling_down or set():
        health.record_failure(p)
    return Router(cfg, health)


def test_explicit_model_passes_through():
    d = make_router().resolve("anything", requested_model="openai/gpt-4o")
    assert d.tier == "explicit"
    assert d.candidates == ["openai/gpt-4o"]


def test_auto_routes_code_tier():
    d = make_router().resolve("fix this bug in the function")
    assert d.tier == "code"
    assert d.candidates[0] == "openrouter/anthropic/claude-3.5-sonnet"


def test_cooling_provider_moves_to_end_not_dropped():
    r = make_router(cooling_down={"openrouter"})
    d = r.resolve("fix this bug in the function")
    # still present (desperate fallback) but the health-aware order flags it
    assert d.candidates == ["openrouter/anthropic/claude-3.5-sonnet",
                            "openrouter/openai/gpt-4o-mini"]
    assert d.skipped == []


def test_unknown_tier_yields_empty_candidates():
    cfg = RouterConfig(providers={}, rules=[], cooldown_s=1)
    d = Router(cfg, HealthRegistry()).resolve("hello")
    assert d.candidates == []
