"""FastAPI entrypoint — OpenAI-compatible endpoint with routing."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import load_config
from .health import HealthRegistry
from .proxy import ProviderError, forward
from .router import Router

app = FastAPI(title="multi-model-llm-router", version="0.1.0")
config = load_config()
health = HealthRegistry(cooldown_s=config.cooldown_s)
router = Router(config, health)


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "providers": {
            name: {
                "available": h.is_available(),
                "consecutive_failures": h.consecutive_failures,
                "last_latency_ms": h.last_latency_ms,
            }
            for name, h in health._health.items()
        },
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    payload = await request.json()
    requested_model = payload.get("model", "auto")
    prompt = next(
        (m.get("content", "") for m in reversed(payload.get("messages", []))
         if m.get("role") == "user"),
        "",
    )

    decision = router.resolve(prompt, requested_model)
    if not decision.candidates:
        return JSONResponse({"error": f"no route for tier '{decision.tier}'"}, status_code=503)

    last_error: ProviderError | None = None
    for candidate in decision.candidates[: config.max_fallbacks]:
        provider_name, model = candidate.split("/", 1)
        provider_cfg = config.providers.get(provider_name)
        if provider_cfg is None:
            continue
        try:
            result = await forward(provider_cfg, model, payload)
            health.record_success(provider_name, result["_meta"]["latency_ms"])
            return JSONResponse(result)
        except ProviderError as exc:
            health.record_failure(provider_name)
            last_error = exc
            continue

    status = last_error.status if last_error else 503
    return JSONResponse(
        {"error": "all candidates failed", "last": str(last_error), "tier": decision.tier},
        status_code=status if status < 500 else 502,
    )
