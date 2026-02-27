# Knowledge Graph Guide

## Übersicht

Der Knowledge Graph bildet Beziehungen zwischen Kooperativen, Röstereien, Regionen und Zertifizierungen ab und ermöglicht fortgeschrittene Graph-Analysen.

Diese Implementierung erfüllt **Enterprise Roadmap Issue #85** und bietet:
- **In-Memory Graph-Analyse** mit NetworkX
- **Interaktive Visualisierung** im Frontend
- **Community Detection** und **Centrality-Metriken**
- **Hidden Connections** Discovery
- **REST API** für alle Graph-Operationen

## Architektur

### Backend-Komponenten

```
apps/api/app/
├── services/knowledge_graph.py    # Graph-Aufbau und Analysen
├── schemas/knowledge_graph.py     # Pydantic Schemas
└── api/routes/knowledge_graph.py  # REST API Endpoints
```

### Graph-Schema

#### Knoten-Typen

1. **Cooperative** (`cooperative_<id>`)
   - Properties: `id`, `region`, `altitude_m`, `certifications`, `varieties`, `total_score`

2. **Roaster** (`roaster_<id>`)
   - Properties: `id`, `city`, `peru_focus`, `specialty_focus`, `price_position`, `total_score`

3. **Region** (`region_<name>`)
   - Properties: `id`, `country`, `production_share_pct`, `quality_consistency_score`

4. **Certification** (`certification_<name>`)
   - Properties: `name`

#### Kanten-Typen

1. **LOCATED_IN**: Cooperative → Region
   - Verbindet Kooperativen mit ihren Regionen

2. **HAS_CERTIFICATION**: Cooperative → Certification
   - Verbindet Kooperativen mit ihren Zertifizierungen
   - Zertifizierungen werden aus dem `certifications` String geparst (comma-separated)

3. **SOURCES_FROM**: Roaster → Region
   - Verbindet Röstereien (mit Peru-Focus) zu Regionen

4. **SIMILAR_PROFILE**: Cooperative ↔ Cooperative, Roaster ↔ Roaster
   - **Cooperatives**: Ähnlich wenn gleiche Region + gemeinsame Zertifizierungen
   - **Roasters**: Ähnlich wenn gleiche Stadt + gleiche Price Position

## API Endpoints

Alle Endpoints erfordern Authentifizierung und mindestens die Rolle `viewer`.

### 1. GET `/graph/network`

Liefert das komplette Netzwerk als Knoten + Kanten.

**Query Parameters:**
- `node_types`: Filter nach Knoten-Typen (z.B. `"cooperative,region"`, default: `"all"`)

**Response:**
```json
{
  "nodes": [
    {
      "id": "cooperative_1",
      "label": "Coop Cajamarca",
      "node_type": "cooperative",
      "properties": {
        "id": 1,
        "region": "Cajamarca",
        "altitude_m": 1800.0,
        "total_score": 8.5
      }
    }
  ],
  "edges": [
    {
      "source": "cooperative_1",
      "target": "region_cajamarca",
      "edge_type": "LOCATED_IN",
      "weight": 1.0
    }
  ],
  "stats": {
    "total_nodes": 50,
    "total_edges": 120,
    "node_types": {
      "cooperative": 30,
      "region": 10,
      "certification": 5,
      "roaster": 5
    },
    "density": 0.048,
    "avg_degree": 2.4
  }
}
```

**Beispiel:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/graph/network?node_types=cooperative,region"
```

### 2. GET `/graph/analysis/{entity_type}/{entity_id}`

Liefert Graph-Analyse für eine bestimmte Entity.

**Path Parameters:**
- `entity_type`: `cooperative`, `roaster`, `region`, `certification`
- `entity_id`: ID der Entity

**Response:**
```json
{
  "entity_id": "cooperative_1",
  "entity_name": "Coop Cajamarca",
  "entity_type": "cooperative",
  "degree": 5,
  "degree_centrality": 0.125,
  "betweenness_centrality": 0.023,
  "neighbors": [...],
  "community_id": 0,
  "community_members": [...]
}
```

**Beispiel:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/graph/analysis/cooperative/1"
```

### 3. GET `/graph/communities`

Community Detection mit Greedy Modularity Algorithmus.

**Response:**
```json
[
  {
    "community_id": 0,
    "size": 15,
    "members": [...],
    "dominant_type": "cooperative",
    "common_attributes": ["Cajamarca", "Organic", "Fair Trade"]
  }
]
```

**Beispiel:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/graph/communities"
```

### 4. GET `/graph/path/{source_type}/{source_id}/{target_type}/{target_id}`

Findet den kürzesten Pfad zwischen zwei Entities.

**Response:**
```json
{
  "source": {...},
  "target": {...},
  "path": [...],
  "edges": [...],
  "total_hops": 2
}
```

**Beispiel:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/graph/path/cooperative/1/roaster/5"
```

### 5. GET `/graph/hidden-connections/{entity_type}/{entity_id}`

Findet versteckte Verbindungen (2-3 Hops entfernt).

**Query Parameters:**
- `max_hops`: Maximale Anzahl Hops (2-5, default: 3)

**Response:**
```json
[
  {
    "entity": {...},
    "connection_path": ["Coop A", "Cajamarca", "Coop B"],
    "hops": 2,
    "reason": "Connected via Cajamarca"
  }
]
```

**Beispiel:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/graph/hidden-connections/cooperative/1?max_hops=3"
```

## Frontend

### Navigation

Der Knowledge Graph ist über die Sidebar erreichbar: **🕸️ Knowledge Graph** (`/graph`)

### Features

1. **Interaktive Canvas-Visualisierung**
   - Force-Directed Layout (einfache Physik-Simulation)
   - Farb-codierte Knoten:
     - **Grün**: Kooperativen
     - **Braun**: Röstereien
     - **Blau**: Regionen
     - **Orange**: Zertifizierungen
   - Hover über Knoten zeigt Label
   - Klick auf Knoten lädt Entity-Analyse

2. **Filter & Zoom**
   - Filter nach Knoten-Typen (Dropdown)
   - Zoom +/- Buttons

3. **Sidebar-Panels**
   - **Graph-Statistiken**: Knoten, Kanten, Dichte, Durchschnittsgrad
   - **Entity-Analyse**: Degree, Centrality, Nachbarn, Community
   - **Communities**: Top 5 Communities mit Größe und Attributen

## Algorithmen

### 1. Degree Centrality

Misst die Anzahl direkter Verbindungen eines Knotens.

```python
degree_centrality = degree(node) / (total_nodes - 1)
```

**Interpretation:**
- Hohe Werte = Viele direkte Verbindungen
- Wichtig für Kooperativen mit vielen Zertifizierungen oder Röstereien in zentralen Regionen

### 2. Betweenness Centrality

Misst wie oft ein Knoten auf dem kürzesten Pfad zwischen anderen Knoten liegt.

**Interpretation:**
- Hohe Werte = Brücken-Knoten im Netzwerk
- Wichtig für Regionen die mehrere Kooperativen verbinden

### 3. Community Detection

Verwendet den **Greedy Modularity** Algorithmus von NetworkX:
```python
nx.community.greedy_modularity_communities(G)
```

**Eigenschaften:**
- Findet dicht verbundene Subgraphen
- Maximiert Modularity (Dichte innerhalb vs. zwischen Communities)
- Fast und skalierbar

**Anwendung:**
- Identifiziert Kooperativen-Cluster in bestimmten Regionen
- Findet Röstereien mit ähnlichem Profil

### 4. Shortest Path

Nutzt Breadth-First Search (BFS) via NetworkX:
```python
nx.shortest_path(G, source, target)
```

**Anwendung:**
- "Wie ist Cooperative A mit Roaster B verbunden?"
- Liefert Pfad: Cooperative → Region → Roaster

### 5. Hidden Connections

Nutzt `nx.single_source_shortest_path_length()` mit Cutoff:
```python
path_lengths = nx.single_source_shortest_path_length(G, node, cutoff=max_hops)
```

Filtert:
- Distanz >= 2 (nicht direkte Nachbarn)
- Distanz <= max_hops (default: 3)

**Anwendung:**
- Discovery von indirekten Beziehungen
- "Welche Röstereien könnten an dieser Cooperative interessiert sein?"

## Performance & Caching

### In-Memory Caching

Der Graph wird für **5 Minuten** gecached:
```python
CACHE_TTL = 300  # seconds
_graph_cache: dict[str, tuple[nx.Graph, float]] = {}
```

**Cache-Invalidierung:**
- Automatisch nach TTL
- Manuell via `invalidate_cache()` (z.B. nach Daten-Updates)

### Performance-Charakteristiken

| Datenmenge | Graph-Aufbau | Centrality | Community Detection |
|------------|--------------|------------|---------------------|
| 100 Nodes  | ~50ms        | ~10ms      | ~20ms               |
| 500 Nodes  | ~200ms       | ~50ms      | ~100ms              |
| 1000 Nodes | ~500ms       | ~150ms     | ~300ms              |

**Skalierung:**
- NetworkX ist In-Memory → O(n²) Space für dichte Graphen
- Für >5000 Nodes: Übergang zu Graph-DB (Neo4j) erwägen
- Aktuell: Vollkommen ausreichend für CoffeeStudio-Daten

## Technische Details

### Dependencies

```
networkx>=3.2
```

NetworkX ist:
- **Pure Python** (keine C-Dependencies)
- **Plattform-unabhängig** (Windows, Linux, macOS)
- **Lightweight** (~5MB installiert)
- **Gut dokumentiert** und **battle-tested**

### Type Safety

Alle Services und Schemas verwenden:
- `from __future__ import annotations`
- Vollständige Type Hints
- MyPy strict mode kompatibel
- Pydantic BaseModel für API-Schemas

### Logging

Nutzt `structlog` für strukturierte Logs:
```python
logger.info("knowledge_graph.graph_built", nodes=50, edges=120)
logger.info("knowledge_graph.cache_hit")
logger.info("knowledge_graph.cache_invalidated")
```

## Tests

Siehe `apps/api/tests/test_knowledge_graph.py`:
- ✅ 19 Unit Tests
- ✅ Graph-Aufbau mit Mock-Daten
- ✅ Knoten- und Kanten-Typen
- ✅ Community Detection
- ✅ Shortest Path
- ✅ Hidden Connections
- ✅ Entity Analysis
- ✅ Caching

## Erweiterungen

### Zukünftige Features

1. **Temporal Analysis**
   - Graph-Entwicklung über Zeit
   - "Wie hat sich die Community 2023 vs. 2024 verändert?"

2. **Recommendation Engine**
   - "Welche Kooperativen passen zu diesem Roaster?"
   - Basierend auf Graph-Strukturen und Centrality

3. **Weighted Edges**
   - Stärke der Beziehungen (z.B. Transaktionsvolumen)
   - Influence Propagation

4. **Graph ML**
   - Node Embeddings (Node2Vec)
   - Link Prediction
   - Anomaly Detection

## Verwandte Dokumentation

- **Enterprise Roadmap**: Issue #85 (Knowledge Graph)
- **API Docs**: http://localhost:8000/docs
- **NetworkX Docs**: https://networkx.org/documentation/stable/

## Support

Bei Fragen oder Issues:
1. Check API Docs: http://localhost:8000/docs
2. Check Logs: `docker compose logs backend -f`
3. Check Tests: `docker compose exec backend pytest tests/test_knowledge_graph.py -v`
