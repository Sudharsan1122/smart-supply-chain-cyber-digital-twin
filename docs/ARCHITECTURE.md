# Architecture — Smart Supply Chain Cyber Digital Twin

## System Overview

The **Smart Supply Chain Cyber Digital Twin** is an API-first cyber-physical platform designed to continuously monitor, evaluate, and secure modern distributed supply chain ecosystems. Across a heterogeneous network of 32 assets—encompassing suppliers, multi-zone regional warehouses, logistics fleets, IoT telemetry sensors, edge vehicle gateways, authentication servers, and central databases—the system synchronizes telemetry streams into a live Directed Acyclic Graph (DAG) state. Through a dual-engine architecture combining deterministic MITRE ATT&CK correlation rules with unsupervised machine-learning anomaly detection (Isolation Forest), the platform identifies zero-day threats, models multi-hop blast radii, enriches threat intelligence indicators, synthesizes attack narratives, and executes automated triage sweeps in real time.

---

## Pipeline Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    SUPPLY CHAIN TELEMETRY SOURCES                                  |
|   Sensors (Temp/Hum/Door)  |  Fleet Trucks (GPS/VGW)  |  Warehouses (WMS)  |  Auth & API Gateways  |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
                                      [ 1. Ingestion Engine ]
                                  (MQTT Broker & REST Ingestion)
                                                  |
                                                  v
                                      [ 2. Digital Twin Graph ]
                                (NetworkX DAG / Twin State Tracking)
                                                  |
                                                  v
                                      [ 3. Detection Engine ]
                                (Rule Engine + Scikit-Learn ML Model)
                                                  |
                                                  v
                                     [ 4. Incident Correlator ]
                                (Cross-Event Pattern & Session Window)
                                                  |
                                                  v
                                      [ 5. Dynamic Risk Engine ]
                               (Graph Centrality + Threat Severity Score)
                                                  |
                                                  v
                                       [ 6. IOC Extractor ]
                                   (IPs, Domains, Hashes, Tokens)
                                                  |
                                                  v
                                     [ 7. Threat Intel Enricher ]
                               (VirusTotal / AbuseIPDB / AlienVault OTX)
                                                  |
                                                  v
                                       [ 8. Attack Storyteller ]
                               (MITRE ATT&CK Tactics & Narrative Synth)
                                                  |
                                                  v
                                       [ 9. Blast Radius Model ]
                             (Dependency Transitive Closure & Impact Depth)
                                                  |
                                                  v
                                      [ 10. Automated Triage ]
                                 (ML Classifier: TP / FP / FN / TN)
                                                  |
                                                  v
                                      [ Flask Dashboard & UI ]
                               (Live Fleet / Stories / Intel / Triage)
```

---

## Component Table

| Package / Module | Description & Role |
| :--- | :--- |
| `api` | FastAPI application layer providing REST endpoints, OpenAPI schemas, lifecycle management, and Swagger UI. |
| `api_sources` | External threat intelligence and environment adapters (VirusTotal, AbuseIPDB, AlienVault OTX, OpenWeather). |
| `attack_story` | Attack timeline builder, tactical mapping (MITRE ATT&CK), story narrative generation, and simulation runner. |
| `config` | Centralized Pydantic application settings, environment resolution, and broker configuration. |
| `dashboard` | Lightweight Flask UI with real-time responsive interfaces for live fleet status, stories, threat intel, and triage. |
| `database` | PostgreSQL persistence layer using SQLAlchemy 2.0 (AsyncIO), connection pooling, ORM models, and repositories. |
| `demo` | End-to-end multi-scenario attack simulation orchestrator (`SIM-01`, `SIM-02`, `SIM-03`) validating system behavior. |
| `detection` | Dual-engine anomaly detection implementing threshold/pattern rules and isolation-forest ML inference. |
| `digital_twin` | Topological asset modeling via NetworkX DAG, node state cache, graph centrality metrics, and blast radius. |
| `ingestion` | MQTT message subscriber, protocol payload normalizer, JSON validation schemas, and incident correlation pipeline. |
| `ml` | Machine learning artifact registry, rolling feature extraction, model serialization, and unsupervised retraining. |

---

## Data Flow (10 Steps)

1. **Telemetry & Event Ingestion**: Cyber-physical telemetry (GPS coordinates, temperatures, door latches, login attempts, API rates) arrives via Mosquitto MQTT or HTTP REST endpoints.
2. **Payload Normalization & Schema Validation**: Ingestion pipelines validate payloads with Pydantic schemas, standardizing timestamps and metric units into canonical formats.
3. **Digital Twin Graph State Synchronization**: Normalized records update in-memory `twin_state` and are recorded into `twin_states` and `state_transitions` tables.
4. **Hybrid Detection Execution**: Every stream slice is simultaneously evaluated by deterministic rule engines (e.g. brute-force, sensor threshold violations) and scikit-learn Isolation Forest ML models.
5. **Multi-Event Incident Correlation**: Correlated events are aggregated into contextual `incidents` based on temporal sliding windows and physical topology proximity.
6. **Graph-Aware Dynamic Risk Scoring**: Asset risk scores are recomputed continuously factoring in threat severity, historical anomaly density, and NetworkX PageRank/eigenvector centrality.
7. **Automated IOC Extraction**: Security events and abnormal payloads are parsed to extract indicators of compromise (IP addresses, domain names, hashes, anomalous API tokens).
8. **External Threat Intelligence Enrichment**: Extracted IOCs are enriched via VirusTotal, AbuseIPDB, and AlienVault OTX adapters with caching and rate limiting.
9. **Attack Story & Blast Radius Synthesis**: Multi-hop dependency traversal computes the downstream impact (blast radius), mapping attacks to MITRE tactics and synthesizing human-readable narratives.
10. **Triage & UI Presentation**: Automated triage sweeps classify detections into True/False Positives, streaming updated metrics and statuses to the Flask Live Fleet Dashboard.

---

## Database Schema (20 Tables)

1. `assets`: Master registry of physical and cyber assets (nodes, types, parent hierarchies, metadata).
2. `telemetry`: High-throughput time-series telemetry metrics received from all connected assets.
3. `security_events`: Granular security events, audit logs, and operational alerts.
4. `twin_states`: Current state, health evaluation, geolocation coordinates, and operational snapshot per asset.
5. `state_transitions`: Historical audit log of every operational and security transition with transition reasons.
6. `detections`: Rule-based and ML-generated anomaly detections with confidence and severity levels.
7. `risk_scores`: Calculated risk score records (0–100) along with contributing factor breakdowns.
8. `attack_scenarios`: Pre-configured attack simulation definitions and behavioral parameters.
9. `attack_stories`: Synthesized multi-stage attack campaigns with root causes and narratives.
10. `iocs`: Extracted Indicators of Compromise (IPs, URLs, domain names, file hashes).
11. `ioc_enrichments`: Third-party threat intelligence verdicts and raw enrichment payloads.
12. `blast_radius`: Computed downstream asset compromise paths and propagation depth records.
13. `triage`: Analyst and automated ML triage verdicts (True Positive, False Positive, FN, TN).
14. `incidents`: Correlated high-severity incident entities grouping related alerts and telemetry.
15. `incident_members`: Association mapping connecting individual telemetry and security events to incidents.
16. `twin_state_snapshots`: Periodic full and delta state snapshots supporting replay and forensics.
17. `transition_anomalies`: Anomaly records flagging unauthorized or out-of-order finite state transitions.
18. `attack_story_events`: Ordered timeline events contributing to an attack campaign.
19. `attack_story_tactics`: MITRE ATT&CK matrix tactics associated with active attack campaigns.
20. `ioc_observations`: Observation frequency and asset context mappings for each discovered IOC.

---

## Design Principles

- **API-First & Headless Core**: All functionality is exposed via clean, documented RESTful APIs with typed Pydantic contracts and OpenAPI specifications.
- **Hybrid Cyber-Physical Modeling**: Security posture is evaluated in tandem with physical operational telemetry (temperature, transit status, door security).
- **Dual-Track Anomaly Detection**: Combines predictable, low-latency deterministic rules with unsupervised ML (Isolation Forest) to capture both known attack signatures and novel zero-day drifts.
- **Topological Risk Propagation**: Asset risk is not evaluated in isolation; NetworkX DAG dependency analysis accounts for upstream bottlenecks and downstream blast radius.
- **Asynchronous Non-Blocking Execution**: Built on modern Python AsyncIO with SQLAlchemy 2.0 async engine and paho-mqtt background thread event bridge.
- **Multi-Tenant / Multi-Cloud Portability**: Encapsulated entirely in standard OCI containers orchestrated via Docker Compose and production Helm/Kubernetes/Terraform targets.
- **Zero-Trust Security & Observability**: Principle of least privilege with non-root container users, structured health probes, and comprehensive audit logs across all 20 relational tables.
