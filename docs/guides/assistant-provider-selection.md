# Assistant Provider Selection (Cloud + Free-Tier Ready)

This project supports multiple LLM providers for `/assistant/*` and `/analyst/*`.

## Provider Modes

- `RAG_PROVIDER=auto` (recommended)
  - Selection order: `openrouter` -> `groq` -> `ollama` -> deterministic fallback
- `RAG_PROVIDER=openrouter`
  - Cloud-hosted, supports free-tier models
- `RAG_PROVIDER=groq`
  - Cloud-hosted, free developer tier
- `RAG_PROVIDER=ollama`
  - Local runtime
- `RAG_PROVIDER=openai`
  - Paid cloud runtime

## Minimal Cloud Setup (No Local LLM)

Use OpenRouter free-tier model:

```env
RAG_PROVIDER=openrouter
RAG_LLM_MODEL=meta-llama/llama-3.3-8b-instruct:free
OPENROUTER_API_KEY=sk-or-...
```

Optional provider-specific default (when `RAG_LLM_MODEL` is empty):

```env
RAG_LLM_MODEL_OPENROUTER=meta-llama/llama-3.3-8b-instruct:free
```

## Auto Mode Setup (Recommended)

```env
RAG_PROVIDER=auto
OPENROUTER_API_KEY=sk-or-...
GROQ_API_KEY=gsk_...
# OLLAMA_BASE_URL=http://localhost:11434
```

## Notes

- Fully unlimited cloud inference is generally not realistic at production scale.
- `auto` gives a practical free/freemium-first path and stable fallback behavior.
- If no provider is available, the deterministic fallback keeps endpoints responsive.