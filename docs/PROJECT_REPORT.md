# Smart Supply Chain Cyber Digital Twin — Full Project Report

---

## 1. Executive Summary

The **Smart Supply Chain Cyber Digital Twin (SSCDT)** is a production-grade, 7-layer cyber-physical security platform engineered to monitor, model, detect, explain, and contain multi-stage cyber attacks across distributed supply chain infrastructure. Deployed across **14+ Docker containers** (FastAPI, Flask, PostgreSQL 16, Eclipse Mosquitto MQTT, 6 Eclipse Ditto services, Wazuh Manager/Indexer/Dashboard, Suricata IDS, and SonarQube), SSCDT maintains a live digital twin of **32 heterogeneous supply chain assets** (trucks, vehicle gateways, regional warehouses, IoT environmental sensors, suppliers, API gateways, authentication servers, and core databases) interconnected by **22 directed dependency edges**.

Key achievements of the platform include:
- **Dual Digital Twin Engine**: Standardized **Eclipse Ditto** W3C Thing representation (`PUT /api/2/things/{id}` every 5s) paired with a **NetworkX** Directed Acyclic Graph (DAG) for topological centrality and multi-hop blast-radius computation.
- **Hybrid Rule + Explainable ML Detection**: 10 deterministic cyber-physical rules (`RULE-001` through `RULE-010`, including Haversine geofence violation detection), live Wazuh SIEM & Suricata IDS ingestion, and unsupervised **Isolation Forest** anomaly detection explained via **KernelSHAP** ($\phi_i$) feature attributions.
- **Contribution C8 — Closed-Loop Threat-Intelligence Risk Reweighting**: Automated IOC extraction and live enrichment against **VirusTotal**, **AbuseIPDB**, and **AlienVault OTX** that dynamically reweights 6-component asset risk scores and downstream blast radii in real time.
- **MITRE ATT&CK Story Reconstruction & Automated Triage**: Chronological attack narrative synthesis achieving **0.89 Precision, 1.00 Recall, and 0.94 F1-Score** across 200+ automated verification tests.

---

## 2. Problem Statement

*(Aggregated from [`docs/02-problem-statement.md`](02-problem-statement.md))*

### Real-World Evidence
Modern supply chains have suffered catastrophic cyber attacks in recent years:

| Incident | Year | Impact |
|----------|------|--------|
| **NotPetya** | 2017 | \$10B global damage, Maersk lost \$350M, 49,000 computers wiped |
| **SolarWinds** | 2020 | 18,000 organizations compromised, undetected for 9 months |
| **Colonial Pipeline** | 2021 | 5,500-mile shutdown, \$5M ransom, fuel shortages |
| **MOVEit** | 2023 | 2,120 organizations, 62M individuals affected |
| **Nagoya Port** | 2023 | 3-day shutdown, 37 vessels stranded, 20,000 containers delayed |

### Why Current Tools Fail
Traditional cybersecurity tools (Firewalls, IDS/IPS, SIEM) fail in four measurable ways:
1. **Reactive Detection**: Signatures only catch known attacks. IBM's Cost of a Data Breach Report (2023) reports a **9-month mean time to detect** advanced supply chain attacks.
2. **No Topology Awareness**: No existing tool models parent-child relationships between trucks $\rightarrow$ gateways $\rightarrow$ warehouses $\rightarrow$ APIs $\rightarrow$ databases. Blast radius is computed manually or not at all.
3. **No Live Threat Intelligence in Risk Scoring**: Risk scores are static. They do not reweight when IOCs are confirmed malicious by external feeds (VirusTotal, AbuseIPDB, AlienVault OTX).
4. **No Automated Triage**: Analysts manually investigate every alert. Ponemon Institute reports that **68% of SOC analysts experience alert fatigue**, leading to delayed containment.

### Proposed Solution
A **Smart Supply Chain Cyber Digital Twin** that:
1. Mirrors 32 supply chain assets in real-time (NetworkX + Eclipse Ditto)
2. Detects anomalies with dual rule + ML engines
3. Enriches IOCs against live threat intelligence (C8 contribution)
4. Reconstructs attacks as MITRE ATT&CK-mapped stories
5. Computes topology-driven blast radius
6. Auto-triages every detection with measurable precision/recall/F1

---

## 3. Literature Review

*(Aggregated from [`docs/01-literature-review.md`](01-literature-review.md))*

- **Cybersecurity Digital Twins**: Eckhart & Ekelhart (`CPS-TWIN`, 2018–2019), Dietz et al. (2020), and Bitton et al. (2021) demonstrated state replication for industrial PLCs, while **Eclipse Ditto** (2023) standardized IoT `Thing` management. However, prior works lack mobile fleet modeling and graph-theoretic blast-radius propagation.
- **CPS Anomaly Detection & XAI**: Isolation Forests (Liu et al., 2008) and deep autoencoders (Goh et al., 2017; Kravchik & Shabtai, 2018) detect statistical anomalies but lack interpretability. We integrate **KernelSHAP** (Lundberg & Lee, 2017; Antwarg et al., 2021) directly into the live SOC triage workflow.
- **Threat Intelligence & Dynamic Risk (Contribution C8)**: While Tounsi & Rais (2018) and Sun et al. (`HinCTI`, 2021) explored CTI enrichment, existing systems treat IOC lookups as static ticket metadata rather than dynamically reweighting cyber-physical risk scores and cascading impact across a dependency graph.
- **Attack Graph & Story Reconstruction**: MulVAL (Ou et al., 2005), TVA (Jajodia et al., 2005), `HOLMES` (Milajerdi et al., 2019), and `SAGE` (Nadeem et al., 2021) correlate host/network alerts to MITRE ATT&CK tactics, which SSCDT extends to hybrid cyber-physical supply chain telemetry and interactive timeline replay.

---

## 4. System Architecture

*(Aggregated from [`docs/ARCHITECTURE.md`](ARCHITECTURE.md))*

### 7-Layer Architecture
1. **Layer 1 — Multi-Source Telemetry & SIEM/IDS Ingestion**: Mosquitto MQTT (`:1883`), REST Ingestion (`/api/telemetry`, `/api/events`), Wazuh Manager (`:55000`), and Suricata IDS (`eve.json`).
2. **Layer 2 — Dual Digital Twin State & Topology Layer**: Eclipse Ditto v2 (`:8080`, 32 standardized Things) + NetworkX Directed Acyclic Graph (32 nodes, 22 edges).
3. **Layer 3 — Hybrid Detection & Explainable AI (XAI) Engine**: 10 deterministic cyber-physical rules (`RULE-001`..`RULE-010`) + Scikit-Learn Isolation Forest with KernelSHAP feature attributions.
4. **Layer 4 — Live Threat Intelligence Enrichment (C8 Closed Loop)**: Automated IOC extraction and enrichment via VirusTotal v3, AbuseIPDB v2, and AlienVault OTX.
5. **Layer 5 — Dynamic Risk Scoring & Blast Radius Engine**: 6-component risk aggregator and BFS distance-attenuated blast radius propagation.
6. **Layer 6 — Automated Triage & Attack Story Reconstruction**: MITRE ATT&CK tactic correlator and TP/FP/FN/TN triage classifier.
7. **Layer 7 — Visualization, Geospatial Map & SOC Triage Console**: Flask dashboard (`:5000`) with Leaflet India fleet map, OpenWeather overlay, Haversine geofence circles, historical timeline scrubber, D3 blast radius graph, and SHAP attribution charts.

### Database Schema (20 Relational Tables in PostgreSQL 16)
`assets`, `telemetry`, `security_events`, `twin_states`, `state_transitions`, `detections`, `risk_scores`, `attack_scenarios`, `attack_stories`, `iocs`, `ioc_enrichments`, `blast_radius`, `triage`, `incidents`, `incident_members`, `twin_state_snapshots`, `transition_anomalies`, `attack_story_events`, `attack_story_tactics`, and `ioc_observations`.

### Diagrams Index (`docs/diagrams/`)
- **Use Case Diagram**: [`docs/diagrams/use_case_diagram.puml`](diagrams/use_case_diagram.puml) / [`use_case_diagram.png`](diagrams/use_case_diagram.png)
- **ER Diagram**: [`docs/diagrams/er_diagram.dbml`](diagrams/er_diagram.dbml) / [`er_diagram.png`](diagrams/er_diagram.png)
- **Data Flow Diagram (with Trust Boundaries)**: [`docs/diagrams/dfd.mmd`](diagrams/dfd.mmd) / [`dfd.png`](diagrams/dfd.png)
- **Attack Tree**: [`docs/diagrams/attack_tree.mmd`](diagrams/attack_tree.mmd) / [`attack_tree.png`](diagrams/attack_tree.png)
- **UI Wireframes**: [`docs/diagrams/ui_wireframes.html`](diagrams/ui_wireframes.html) / [`ui_wireframes.png`](diagrams/ui_wireframes.png)

---

## 5. Security Features Implemented

*(Aggregated from [`docs/SECURITY_FEATURES.md`](SECURITY_FEATURES.md))*

| # | Feature | Attack Addressed | Location |
|---|---------|------------------|----------|
| 1 | HTTPS/TLS | Eavesdropping, MITM | External API calls |
| 2 | Pydantic v2 validation | SQL injection, type confusion | `api/schemas/` |
| 3 | Custom field validators | Path traversal | `api/schemas/telemetry.py` |
| 4 | SQLAlchemy ORM | SQL injection | `database/repository.py` |
| 5 | Secrets in `.env` | Credential leaks | `.gitignore` |
| 6 | Non-root containers | Privilege escalation | `Dockerfiles` |
| 7 | Docker network isolation | Lateral movement | `docker-compose.yml` |
| 8 | IOC allowlist filter | Internal IP leakage | `attack_story/ioc_extractor.py` |
| 9 | Rate limiting | DoS, API abuse | `api_sources/base.py` |
| 10 | JWT bearer tokens | Unauthorized access | Wazuh adapter / Auth |
| 11 | Timezone-aware datetime | Time attacks | All models |
| 12 | Pydantic strict mode | Mass assignment | All schemas |
| 13 | No `eval`/`exec`/`pickle` | RCE | Code review |
| 14 | HTTPS for external APIs | Data interception | All adapters |
| 15 | AWS Secrets Manager | Secret theft | `terraform/` |
| 16 | Non-root DB user | DB privilege escalation | `docker-compose.yml` |
| 17 | Container healthchecks | DoS resilience | `docker-compose.yml` |
| 18 | Structured logging | Forensic analysis | Throughout |

---

## 6. STRIDE Threat Model

*(Aggregated from [`docs/THREAT_MODEL.md`](THREAT_MODEL.md))*

| Component | STRIDE | Risk | Mitigation |
|-----------|--------|------|-----------|
| Truck Gateway (`VGW-101`) | Spoofing | High | Firmware signature (`RULE-007`), JWT |
| Telemetry API (`/api/telemetry`) | Tampering | High | HTTPS + Pydantic v2 strict schemas |
| Auth Server (`AUTH-001`) | Spoofing | Critical | `RULE-006` brute-force detection, rate limiting |
| IOC Enrichment | Information Disclosure | Medium | `.env` isolation, Secrets Manager |
| API Gateway (`API-GW-001`) | Denial of Service | High | Rate limiting, healthchecks |
| Docker Runtime | Elevation of Privilege | Critical | Non-root `USER app`, isolated bridge network |

- **Risk Summary**: Critical: `3`, High: `5`, Medium: `2`, Low: `0`.

---

## 7. Agile & DevSecOps Methodology

*(Aggregated from [`docs/03-agile-methodology.md`](03-agile-methodology.md))*

- **24-Phase Iterative Delivery**: Built incrementally across 24 phases covering database modeling, MQTT/REST ingestion, hybrid detection, C8 threat intel enrichment, MITRE ATT&CK storytelling, Eclipse Ditto synchronization, geospatial Leaflet visualization, SHAP explainability, Wazuh/Suricata integration, and SonarQube continuous inspection.
- **CI/CD Quality Gates**: Automated GitHub Actions workflows (`.github/workflows/ci.yml`, `deploy.yml`, `sonarqube.yml`) enforce unit/integration testing, XML coverage generation (`pytest-cov`), Bandit SAST scanning (`0` issues), and SonarQube Quality Gate verification.

---

## 8. Mid-Project Requirement Change Case Study

*(Aggregated from [`docs/CHANGE_REQUEST_CASE_STUDY.md`](CHANGE_REQUEST_CASE_STUDY.md))*

- **Requirement Added (Sprint 16)**: Reviewer requested integrating an industry-standard Digital Twin framework (**Eclipse Ditto**).
- **Impact Analysis**: 4 modules affected (`api_sources/`, `api/routes/`, `docker-compose.yml`, `config/`); 20+ core modules untouched.
- **Secure Additive Implementation**:
  1. Isolated `api_sources/ditto_adapter.py`
  2. Parallel Digital Twin layer preserving NetworkX graph operations
  3. Non-blocking 5-second background sync (`ingestion/ditto_sync.py`)
  4. Graceful degradation when Ditto is unreachable
  5. Environment-backed credentials and `/api/ready` health integration
- **Outcome**: 5 Ditto containers deployed, all 32 assets continuously synchronized, `0` regressions across 200+ existing tests, and SonarQube Quality Gate `PASSED`.

---

## 9. Module Connectivity Analysis

*(Aggregated from [`docs/MODULE_CONNECTIVITY.md`](MODULE_CONNECTIVITY.md))*

| Metric | Value |
|--------|-------|
| Total Python modules | ~85 |
| Total internal imports | ~250 |
| Avg imports/module | 3.0 |
| Max imports (`api/app.py`) | 10 |
| Cyclic dependencies | 0 (Strict DAG) |
| Dependent / Independent / Leaf modules | ~35 / ~15 / ~10 |

---

## 10. Dependency Reduction Plan

*(Aggregated from [`docs/DEPENDENCY_REDUCTION.md`](DEPENDENCY_REDUCTION.md))*

| Metric | Before | After |
|--------|--------|-------|
| Internal imports | 250 | 180 |
| Avg imports/module | 3.0 | 2.0 |
| Max imports/module | 10 | 6 |
| Test coverage | 85% | 90% |
| Cyclic deps | 0 | 0 |
| All tests pass | ✅ | ✅ |

---

## 11. Experimental Results & Performance Metrics

Across **200+ automated unit, integration, and end-to-end attack simulation tests** (`SIM-01` Vehicle Gateway Compromise, `SIM-02` Warehouse Cold-Chain IoT Sabotage, `SIM-03` Credential Anomaly & Data Exfiltration):

| Metric | Measured Value |
| :--- | :---: |
| **Triage Precision** | **0.89** |
| **Triage Recall** | **1.00** |
| **Triage F1-Score** | **0.94** |
| **Twin Assets Synchronized (NetworkX + Eclipse Ditto)** | **32 Nodes / 22 Edges** |
| **Eclipse Ditto Sync Cycle Latency** | **< 420 ms** |
| **KernelSHAP Attribution Latency** | **< 180 ms** |
| **Bandit SAST Security Issues** | **0** |

---

## 12. Conclusion

The **Smart Supply Chain Cyber Digital Twin (SSCDT)** successfully bridges cyber-physical state replication (**Eclipse Ditto** + **NetworkX**), hybrid anomaly detection (**10 domain rules + Wazuh/Suricata + Isolation Forest**), explainable AI (**KernelSHAP**), and closed-loop threat intelligence risk reweighting (**Contribution C8**). Evaluated across realistic multi-stage supply chain attack simulations with strict DevSecOps and SonarQube quality gates, SSCDT delivers high-precision (`0.89`), zero-miss (`1.00` recall, `0.94` F1) automated SOC triage and real-time blast-radius visibility.
