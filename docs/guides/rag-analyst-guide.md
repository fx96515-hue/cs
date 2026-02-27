# RAG AI Analyst Guide (Multi-Provider Architecture)

## Übersicht

Der RAG (Retrieval-Augmented Generation) KI-Analyst ist eine conversational AI für die CoffeeStudio-Plattform. Nutzer können in natürlicher Sprache (Deutsch/Englisch) Fragen über Kooperativen, Röstereien, Marktdaten und Sourcing stellen.

**NEU in v2.0:** Multi-Provider-Architektur mit Ollama als Standard – **funktioniert ohne API Key!**

## Architektur

The RAG service uses pgvector semantic search to retrieve relevant context from cooperatives and roasters, then passes this context to an LLM (Ollama/OpenAI/Groq) to generate answers grounded in the actual data.

## Installation & Setup

### Option 1: Ollama (Standard, kein API Key)

1. **Ollama installieren:**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Ollama starten:**
   ```bash
   ollama serve
   ```

3. **Modell herunterladen:**
   ```bash
   ollama pull llama3.1:8b
   ```

4. **CoffeeStudio konfigurieren (.env):**
   ```bash
   RAG_PROVIDER=ollama
   RAG_LLM_MODEL=llama3.1:8b
   OLLAMA_BASE_URL=http://localhost:11434
   ```

### Option 2: OpenAI (Cloud)

1. API Key generieren: https://platform.openai.com/api-keys

2. **CoffeeStudio konfigurieren (.env):**
   ```bash
   RAG_PROVIDER=openai
   RAG_LLM_MODEL=gpt-4o-mini
   OPENAI_API_KEY=sk-...
   ```

### Option 3: Groq (Cloud, schnell)

1. API Key generieren: https://console.groq.com/keys

2. **CoffeeStudio konfigurieren (.env):**
   ```bash
   RAG_PROVIDER=groq
   RAG_LLM_MODEL=llama-3.1-70b-versatile
   GROQ_API_KEY=gsk_...
   ```

## Konfiguration

```bash
# LLM Provider
RAG_PROVIDER=ollama                    # ollama | openai | groq
RAG_LLM_MODEL=llama3.1:8b              # Provider-specific
RAG_TEMPERATURE=0.3                    # 0.0-1.0

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI
OPENAI_API_KEY=sk-...

# Groq
GROQ_API_KEY=gsk_...

# RAG Settings
RAG_MAX_CONTEXT_ENTITIES=10            # Max entities for context
RAG_MAX_CONVERSATION_HISTORY=20        # Max chat history
```

## API Endpoints

### POST /analyst/ask

```bash
curl -X POST http://localhost:8000/analyst/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Welche Kooperativen in Cajamarca haben Fair Trade?",
    "conversation_history": []
  }'
```

**Rate Limit:** 20 Requests/Minute

### GET /analyst/status

```bash
curl -X GET http://localhost:8000/analyst/status \
  -H "Authorization: Bearer $TOKEN"
```

## Frontend-Nutzung

1. Navigiere zu `/analyst` in der Sidebar unter "🤖 KI-Analyst"
2. Das Chat-Interface öffnet sich mit Beispielfragen
3. Quellenangaben sind klickbare Links zu Entity-Detailseiten

## Troubleshooting

### Ollama: "Service nicht verfügbar"

```bash
# Prüfe ob Ollama läuft:
ollama list

# Starte Ollama:
ollama serve

# Restart Backend:
docker-compose restart backend
```

### Keine Embeddings

```bash
# Embeddings generieren:
curl -X POST http://localhost:8000/enrich/cooperatives/embeddings \
  -H "Authorization: Bearer $TOKEN"
```

### Rate Limit erreicht

- Warte 1 Minute (20 Requests/Minute)
- Bei Bedarf: Erhöhe Limit in `apps/api/app/api/routes/rag_analyst.py`

## Performance & Kosten

**Ollama:** Kostenlos (nur Hardware)
**OpenAI (gpt-4o-mini):** ~$0.001-0.003 pro Frage
**Groq:** Günstiger als OpenAI

## Sicherheit

- Authentifizierung erforderlich (`Authorization: Bearer $TOKEN`)
- Rate Limiting (20/min via slowapi)
- Input Validation (max 1000 chars)
- Keine API Keys in Responses

## Support

- **API Docs:** http://localhost:8000/docs
- **Logs:** `docker-compose logs backend`
- **Issues:** GitHub Issues

---

**Version:** 2.0.0  
**Letzte Aktualisierung:** 2026-02-13
