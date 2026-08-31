# Multi-Model LLM Router

[![CI](https://github.com/devviniciusfmk-sys/multi-model-llm-router/actions/workflows/ci.yml/badge.svg)](https://github.com/devviniciusfmk-sys/multi-model-llm-router/actions/workflows/ci.yml)

Dynamic LLM routing layer that selects the best model per request — balancing quality, latency and cost across providers (Claude, GPT, Llama, DeepSeek and others) behind a single OpenAI-compatible API.

> **Note:** a from-scratch reference build of the routing pattern I run in production daily. Provider credentials and internal quotas are not included.

## How it works

```
Client (OpenAI-compatible) → Router API → classify task → pick model
                                │
                                ├── task rules: code / writing / reasoning / cheap
                                ├── health check per provider (cooldown on 429/5xx)
                                └── fallback chain: primary → secondary → cheapest
```

- **Task classification** — keyword + heuristic rules decide the tier (reasoning, code, writing, bulk/cheap).
- **Provider health** — failing providers enter cooldown and are probed before rejoining the pool.
- **Fallback chain** — every request has an ordered fallback list; a dead provider never fails a request.
- **Cost awareness** — bulk tasks route to free/cheap tiers; complex tasks escalate to premium models.

## Stack

Python · FastAPI · httpx · Pydantic · pytest

## Run locally

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=your-key   # or any OpenAI-compatible endpoints
uvicorn app.main:app --reload --port 3000
```

```bash
curl http://localhost:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Refactor this SQL..."}]}'
```

`model: "auto"` triggers routing; any explicit model name is proxied as-is.

## Status

Routing core, health/cooldown and fallback chain implemented and covered by unit tests. Provider registry is config-driven (YAML).
