from app.health import HealthRegistry


def test_new_provider_is_available():
    h = HealthRegistry(cooldown_s=120)
    assert h.get("openrouter").is_available()


def test_failure_triggers_cooldown():
    h = HealthRegistry(cooldown_s=120)
    h.record_failure("openrouter")
    assert not h.get("openrouter").is_available()


def test_success_clears_cooldown():
    h = HealthRegistry(cooldown_s=120)
    h.record_failure("openrouter")
    h.record_success("openrouter", latency_ms=350.0)
    assert h.get("openrouter").is_available()
    assert h.get("openrouter").consecutive_failures == 0


def test_backoff_grows_with_consecutive_failures():
    h = HealthRegistry(cooldown_s=100)
    h.record_failure("a")
    first_until = h.get("a").cooldown_until
    h.record_failure("a")
    second_until = h.get("a").cooldown_until
    assert second_until - first_until >= 100  # 2x window
    assert h.get("a").consecutive_failures == 2


def test_available_providers_filters_cooling_down():
    h = HealthRegistry(cooldown_s=120)
    h.record_success("good", 100.0)
    h.record_failure("bad")
    assert h.available_providers() == ["good"]
