# Agile & Secure SDLC Methodology — Smart Supply Chain Cyber Digital Twin

## 1. Iterative 24-Phase Agile Delivery
The Smart Supply Chain Cyber Digital Twin (SSCDT) was developed across 24 iterative sprints/phases following an Agile + DevSecOps methodology:

| Sprint / Phase Group | Focus Area | Key Deliverables |
| :--- | :--- | :--- |
| **Phases 1–4** | Core Foundation & Data Layer | PostgreSQL 16 schema (20 tables), SQLAlchemy 2.0 async ORM, 32 seeded supply chain assets, NetworkX DAG topology |
| **Phases 5–8** | Ingestion & Hybrid Detection | Mosquitto MQTT bridge, Pydantic v2 validation, normalizer, 10 deterministic domain rules (`RULE-001`..`RULE-010`), Isolation Forest ML |
| **Phases 9–12** | Correlation, Risk & CTI (C8) | Sliding-window incident correlator, 6-component dynamic risk scoring, IOC extraction, VirusTotal/AbuseIPDB/OTX enrichment |
| **Phases 13–16** | Attack Story, Blast Radius & Ditto | MITRE ATT&CK narrative synthesizer, BFS blast-radius propagation, automated triage classifier, Eclipse Ditto v2 integration (Sprint 16 CR) |
| **Phases 17–20** | Geospatial UI & Explainable AI | Flask SOC dashboard, Leaflet India fleet map, OpenWeather overlay, Haversine geofencing, timeline playback, KernelSHAP XAI |
| **Phases 21–24** | SIEM/IDS, DevSecOps & Quality | Wazuh HIDS + Suricata NIDS containers, Bandit SAST, SonarQube Quality Gate, CI/CD GitHub Actions pipelines, CR-001 Partner Sharing |

## 2. DevSecOps & Continuous Integration Pipeline
Every commit and pull request triggers automated verification gates:
1. **Static Application Security Testing (SAST)**: Bandit scans all Python modules (`0` high/medium/low issues).
2. **Dependency Auditing**: `pip-audit` verifies pinned dependencies in `requirements.txt`.
3. **Automated Test Suite**: 200+ unit, integration, and attack simulation tests executed via `pytest` with `pytest-cov` XML coverage reporting ($\ge 85\%$ threshold).
4. **SonarQube Continuous Inspection**: `.github/workflows/sonarqube.yml` enforces `0` Bugs, `0` Vulnerabilities, `0` Code Smells, and Quality Gate `PASSED`.
