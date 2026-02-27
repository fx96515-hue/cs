# pgvector Semantic Search Implementation Guide

## Overview
This document describes the pgvector-based semantic search implementation for Cooperatives and Roasters (Enterprise Roadmap Step 2, Issue #116).

## Architecture

### Components
1. **pgvector Extension** - PostgreSQL vector similarity search
2. **Local Embeddings** - sentence-transformers `all-MiniLM-L6-v2` (384 dimensions, free/local, CPU-only)
3. **Embedding Service** - Sync generation with graceful degradation
4. **Celery Tasks** - Background embedding generation and backfill
5. **REST API** - Semantic search and similarity endpoints
6. **Frontend UI** - Search page with filters and results

### Data Flow
```
Entity Create/Update → Queue Celery Task → Generate Embedding → Store in DB
Search Query → Generate Query Embedding → pgvector Similarity Search → Return Results
```

## Configuration

### Environment Variables
```bash
# Embedding provider: "local" (default, CPU-only sentence-transformers) or "openai"
EMBEDDING_PROVIDER=local

# Model name (must match the vector(384) column dimension)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: override the HuggingFace model cache directory
# SENTENCE_TRANSFORMERS_CACHE=/path/to/cache

# OpenAI settings – kept for optional use, not required for "local" provider
# OPENAI_API_KEY=sk-...
```

No external API key is required when using the default `local` provider.

### Database Setup
The migration `0013_add_pgvector_embeddings.py` adds the pgvector extension and embedding columns.
Migration `0014_resize_embedding_to_384.py` resizes the columns to `vector(384)` and recreates HNSW indexes for the local model.

## Running the Backfill

To populate embeddings for all existing entities that have no embedding yet:

```bash
# Via Python (one-off, runs inside the worker process)
celery -A app.workers.celery_app.celery call app.workers.tasks.generate_embeddings

# Or programmatically from a Python shell / script
from app.workers.tasks import generate_embeddings

generate_embeddings.delay()                                  # both types, batch_size=50
generate_embeddings.delay(entity_type="cooperative")         # cooperatives only
generate_embeddings.delay(entity_type="roaster", batch_size=100)
```

Progress is logged at `INFO` level; check the Celery worker stdout/logs.

## API Endpoints

### Semantic Search
```http
GET /search/semantic?q={query}&entity_type={type}&limit={n}
```

**Parameters:**
- `q`: Search query text (required)
- `entity_type`: "all", "cooperative", or "roaster" (default: "all")
- `limit`: Max results (default: 10, max: 50)

**Response:**
```json
{
  "query": "organic coffee from Peru",
  "entity_type": "all",
  "results": [
    {
      "entity_type": "cooperative",
      "entity_id": 42,
      "name": "Cooperativa Agraria Cafetalera",
      "similarity_score": 0.89,
      "region": "Cajamarca",
      "certifications": "Organic, Fair Trade",
      "total_score": 85.5
    }
  ],
  "total": 1
}
```

### Find Similar Entities
```http
GET /search/entity/{entity_type}/{entity_id}/similar?limit={n}
```

**Parameters:**
- `entity_type`: "cooperative" or "roaster"
- `entity_id`: Entity ID
- `limit`: Max results (default: 5, max: 50)

**Response:**
```json
{
  "entity_type": "cooperative",
  "entity_id": 42,
  "entity_name": "Cooperativa Agraria Cafetalera",
  "similar_entities": [
    {
      "entity_id": 43,
      "name": "Similar Cooperative",
      "similarity_score": 0.92,
      "region": "Junín",
      "certifications": "Organic"
    }
  ],
  "total": 1
}
```

## Celery Tasks

### Generate Embeddings (Backfill / Batch)
```python
from app.workers.tasks import generate_embeddings

# Generate embeddings for all entities without them
generate_embeddings.delay()

# Generate for specific entity type
generate_embeddings.delay(entity_type="cooperative", batch_size=50)
```

### Update Single Entity Embedding
```python
from app.workers.tasks import update_entity_embedding

# Auto-triggered on entity create/update
update_entity_embedding.delay("cooperative", 42)
```

## Frontend Usage

### Access
Navigate to `/search` or click "🔍 Suche" in the sidebar.

### Features
1. **Search** - Enter natural language query
2. **Filter** - Select entity type (all/cooperatives/roasters)
3. **Results** - View similarity scores and entity details
4. **Find Similar** - Click button to see similar entities

## Graceful Degradation

### Without sentence-transformers installed
- API returns HTTP 503 with helpful error message
- Entity create/update succeeds (embedding task fails silently)
- No crashes or application errors
- Existing fuzzy matching (Levenshtein) remains available

### Testing Without Model Download
```bash
# Run unit tests – model is mocked, no download needed
cd apps/api && pytest tests/ -m "not slow" -v

# Should return 503 when sentence-transformers is not installed
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/search/semantic?q=test"
```

## Performance

### Query Performance
- HNSW index: O(log N) similarity search
- Typical query time: <100ms for 10k entities

### Embedding Generation
- Single embedding: ~200ms
- Batch of 50: ~2-3 seconds
- Generated asynchronously via Celery

## Monitoring

### Check Embedding Coverage
```sql
-- Count entities with/without embeddings
SELECT 
  'cooperatives' as type,
  COUNT(*) as total,
  COUNT(embedding) as with_embedding,
  COUNT(*) - COUNT(embedding) as without_embedding
FROM cooperatives
UNION ALL
SELECT 
  'roasters',
  COUNT(*),
  COUNT(embedding),
  COUNT(*) - COUNT(embedding)
FROM roasters;
```

### Generate Missing Embeddings
```python
# Via Celery task
from app.workers.tasks import generate_embeddings
generate_embeddings.delay()
```

## Security

### API Key Security
- Never commit API keys to version control
- Use environment variables or secrets manager
- Rotate keys regularly
- Monitor API usage

### Input Validation
- Query text: max 500 characters
- Entity type: validated enum
- Limit: capped at 50 results
- SQL injection: protected via parameterized queries

## Testing

### Unit Tests
```bash
# Run embedding service tests
pytest tests/unit/test_embedding_service.py -v
```

### Integration Tests
```bash
# Test semantic search API
curl -X GET "http://localhost:8000/search/semantic?q=test" \
  -H "Authorization: Bearer <token>"

# Test similar entities
curl -X GET "http://localhost:8000/search/entity/cooperative/1/similar" \
  -H "Authorization: Bearer <token>"
```

## Troubleshooting

### Issue: 503 Error on Search
**Cause:** `sentence-transformers` package not installed or model not available
**Solution:** Install dependencies (`pip install sentence-transformers`) and ensure model is downloaded

### Issue: No Results Found
**Cause:** Entities don't have embeddings yet
**Solution:** Run `generate_embeddings` task

### Issue: Slow Queries
**Cause:** Missing or inefficient index
**Solution:** Verify HNSW index exists:
```sql
SELECT * FROM pg_indexes WHERE tablename IN ('cooperatives', 'roasters');
```

### Issue: Celery Task Fails
**Cause:** sentence-transformers model not available or memory constraints
**Solution:** Check logs, verify model download, retry with backoff

## Future Enhancements

1. **RAG AI Analyst** (Step 3)
   - Use embeddings for context retrieval
   - Semantic knowledge base search
   
2. **Duplicate Detection**
   - Replace/augment Levenshtein with semantic similarity
   - Lower threshold for better recall
   
3. **Recommendation Engine**
   - Suggest cooperatives to roasters based on preferences
   - Suggest roasters to cooperatives for outreach
   
4. **Multilingual Search**
   - sentence-transformers multilingual models available
   - Switch model via `EMBEDDING_MODEL` env var

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [sentence-transformers all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
