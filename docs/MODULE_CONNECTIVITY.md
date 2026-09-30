# Module Connectivity Analysis

## Dependency Map (DAG — no cycles)

## Module Categories

### Independent Modules (5)
- config/ (settings only)
- dashboard/templates/
- dashboard/static/
- scripts/
- docs/

### Leaf Modules (4)
- api/schemas/ (depends on config)
- ml/models.py (sklearn only)
- api_sources/base.py (httpx only)
- temporal/machines.py (no deps)

### Core Modules (4)
- database/db.py → config
- digital_twin/graph.py → database
- detection/rules.py → schemas
- digital_twin/metrics.py → graph

### Service Modules (6)
- ingestion/pipeline.py → 8 modules
- ingestion/correlator.py → 3 modules
- attack_story/runner.py → 5 modules
- attack_story/enrichment.py → 4 modules
- digital_twin/blast_radius.py → 3 modules
- detection/triage.py → 4 modules

### Entry Point Modules (22+)
- api/app.py → 10 modules
- api/routes/*.py → 3-8 each
- dashboard/app.py → 4 modules
- demo/orchestrator.py → 5 modules

## Statistics
| Metric | Value |
|--------|-------|
| Total Python modules | ~85 |
| Total internal imports | ~250 |
| Avg imports/module | 3.0 |
| Max imports (api/app.py) | 10 |
| Cyclic dependencies | 0 |

## Dependency Visualization

```mermaid
flowchart TD
    subgraph Entry["Entry Point Modules"]
        APP["api/app.py"]
        ROUTES["api/routes/*.py"]
        DASH["dashboard/app.py"]
        DEMO["demo/orchestrator.py"]
    end

    subgraph Service["Service Modules"]
        PIPE["ingestion/pipeline.py"]
        CORR["ingestion/correlator.py"]
        RUN["attack_story/runner.py"]
        ENR["attack_story/enrichment.py"]
        BLAST["digital_twin/blast_radius.py"]
        TRI["detection/triage.py"]
    end

    subgraph Core["Core Modules"]
        DB["database/db.py"]
        GRAPH["digital_twin/graph.py"]
        RULES["detection/rules.py"]
        MET["digital_twin/metrics.py"]
    end

    subgraph Leaf["Leaf & Independent Modules"]
        CFG["config/settings.py"]
        SCH["api/schemas/"]
        ML["ml/models.py"]
        BASE["api_sources/base.py"]
        TEMP["temporal/machines.py"]
    end

    APP --> ROUTES
    APP --> PIPE
    APP --> DB
    ROUTES --> PIPE
    ROUTES --> RUN
    ROUTES --> ENR
    ROUTES --> BLAST
    ROUTES --> TRI
    DASH --> APP
    DEMO --> APP

    PIPE --> CORR
    PIPE --> RULES
    PIPE --> GRAPH
    PIPE --> DB
    RUN --> PIPE
    ENR --> BASE
    ENR --> DB
    BLAST --> GRAPH
    BLAST --> MET
    TRI --> RULES
    TRI --> ML

    DB --> CFG
    GRAPH --> DB
    RULES --> SCH
    MET --> GRAPH
    SCH --> CFG
```

## Dependent vs Independent
- **Dependent modules:** ~35
- **Independent modules:** ~15
- **Leaf modules:** ~10
