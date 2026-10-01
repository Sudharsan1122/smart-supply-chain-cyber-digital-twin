# Jira Scrum Project Setup & Traceability Guide — SSCDT

**Project:** Smart Supply Chain Cyber Digital Twin (20CYS495 — Project Phase-I)  
**Institution:** Amrita Vishwa Vidyapeetham, Chennai  
**Team Members:** Sudharsan S (`CH.SC.U4CYS23045`), Manojkumar A (`CH.SC.U4CYS23022`)  
**Faculty Guide:** Dr. S. Udhayakumar  
**Jira Cloud Instance:** [https://mastersudhan1234.atlassian.net](https://mastersudhan1234.atlassian.net)  
**GitHub Repository:** [Sudharsan1122/smart-supply-chain-cyber-digital-twin](https://github.com/Sudharsan1122/smart-supply-chain-cyber-digital-twin)  

---

## 1. Project Specifications

| Attribute | Value |
|:---|:---|
| **Project Type** | Scrum (Software Project) |
| **Project Name** | Smart Supply Chain Cyber Digital Twin |
| **Project Key** | `SSCDT` |
| **Project Lead** | Sudharsan S |
| **Default Assignee** | Sudharsan S |
| **Workflow** | `To Do` → `In Progress` → `In Review` → `Done` |
| **Story Points Estimation** | Fibonacci Scale (1, 2, 3, 5, 8, 13, 21) |
| **Total Scope** | 10 Epics, 39 User Stories, 329 Story Points across 2 Sprints |

---

## 2. Components & Labels Taxonomy

### Components (10)
- `Ingestion`: Data ingestion pipelines (REST, MQTT, Wazuh SIEM, Suricata IDS, PostgreSQL storage).
- `Digital Twin Core`: NetworkX DiGraph, live state manager, drift audit, time-travel snapshots, Eclipse Ditto W3C integration.
- `Detection Engine`: 10 rule-based detectors (`RULE-001`..`RULE-010`), finite state machines, multi-signal correlation, 6-component risk engine.
- `Threat Intelligence`: 11 IOC extraction types, 3-provider reputation enrichment (VirusTotal, AbuseIPDB, AlienVault OTX), C8 risk reweighting loop.
- `Analysis & Triage`: BFS blast radius with $0.7^{\text{depth}}$ attenuation, MITRE ATT&CK attack storytelling, automated triage classifier ($F_1=0.94$), KernelSHAP XAI.
- `Dashboard & UI`: Flask UI, responsive Chart.js and D3 views, Leaflet India geographic fleet map, timeline scrubber, Haversine geofences, weather overlay.
- `Machine Learning`: 16 unsupervised ML models (Isolation Forest + One-Class SVM), ML-ANOMALY pipeline integration, KernelSHAP attribution.
- `Infrastructure & DevOps`: 14 Docker containers, multi-stage non-root Dockerfiles, GitHub Actions CI/CD pipelines, AWS Terraform IaC.
- `Security & Compliance`: 20 defense-in-depth requirements (SR1–SR20), STRIDE threat model, SIEM/IDS integration, SAST vulnerability scanning.
- `Documentation`: Software Requirements Specification (53 requirements), ~200 pytest test cases ($\ge 85\%$ coverage), 11 architectural markdown guides.

### Labels (14)
`phase-1`, `phase-2`, `ml`, `ioc`, `c8`, `mitre`, `eclipse-ditto`, `xai`, `wazuh`, `suricata`, `terraform`, `docker`, `testing`, `research`

---

## 3. Epics Structure (10 Epics)

| Epic Key | Epic Name | Component | Priority | Scope & Requirements Covered |
|:---|:---|:---|:---:|:---|
| **EPIC-1** | Ingestion & Data Layer | Ingestion | High | Ingestion via REST, MQTT, Wazuh SIEM, Suricata IDS; PostgreSQL 16 (20 tables, 32 seeded assets). (FR1–FR5, Phases 1, 2, 4, 5, 6) |
| **EPIC-2** | Digital Twin Core | Digital Twin Core | High | NetworkX DiGraph (32 nodes, 14 edges), live state manager, drift auto-reconcile, Eclipse Ditto (32 things), time-travel snapshots. (FR6–FR9, Phases 3, 8, 9, 20) |
| **EPIC-3** | Detection Engine | Detection Engine | High | 10 rule detectors (`RULE-001`..`010`), 9 asset state machines, 6 correlation rules, 6-component risk engine. (FR10–FR12, Phases 7, 10, 11, 12) |
| **EPIC-4** | Threat Intelligence (C8) | Threat Intelligence | Highest | 11 IOC types, VirusTotal/AbuseIPDB/OTX consensus enrichment, closed-loop C8 risk reweighting (**Core Novelty**). (FR13–FR15, Phases 15, 16) |
| **EPIC-5** | Analysis & Triage | Analysis & Triage | Highest | Topological blast radius, MITRE ATT&CK story engine, automated triage ($P=0.89, R=1.00, F_1=0.94$), KernelSHAP XAI. (FR16–FR18, Phases 14, 17, 18, 22) |
| **EPIC-6** | Dashboard & Visualization | Dashboard & UI | High | 4-tab Flask dashboard, Leaflet India highway tracking, timeline playback, Haversine geofences, weather overlay. (FR19–FR23, Phase 19) |
| **EPIC-7** | Machine Learning | Machine Learning | High | 16 unsupervised models (Isolation Forest + One-Class SVM), ML-ANOMALY pipeline integration, SHAP explainability. (Phase 22) |
| **EPIC-8** | Infrastructure & DevOps | Infrastructure & DevOps | Medium | 14 Docker containers, multi-stage non-root builds, GitHub Actions CI/CD, AWS Terraform cloud deployment. (Phases 23, 24) |
| **EPIC-9** | Security & Compliance | Security & Compliance | Medium | 20 security requirements (SR1–SR20), STRIDE threat model, SIEM/IDS integration, Bandit/pip-audit/safety scans. |
| **EPIC-10** | Testing & Documentation | Documentation | Medium | ~200 tests ($\ge 85\%$ coverage), 11 architectural documentation files, 53 requirements documented in SRS. (Phase 21) |

---

## 4. Sprint Execution Plan

### Sprint 1: "Foundation & Detection"
- **Duration:** 2 Weeks (Sprint 1)
- **Goal:** Deliver secure ingestion (REST + MQTT), the NetworkX + Eclipse Ditto digital twin, 10 rule-based detectors, 9 state machines, 6 correlation rules, 6-component risk scoring, and 16 ML models.
- **Committed Stories:** US-01 through US-15, US-27, US-28, US-29 (18 User Stories)
- **Total Story Points:** 143 Points
- **Status:** **DONE** (Implemented & Verified in Review 1 & 2)

### Sprint 2: "Intelligence, Analysis & Ops"
- **Duration:** 2 Weeks (Sprint 2)
- **Goal:** Deliver the C8 threat-intel reweighting loop, blast radius, MITRE-mapped attack stories, auto-triage ($P=0.89, R=1.00, F_1=0.94$), SHAP XAI, 4-tab dashboard with live geo map, 14 Docker containers, AWS Terraform, ~200 tests $\ge 85\%$ coverage, and 11 docs.
- **Committed Stories:** US-16 through US-26, US-30 through US-39 (21 User Stories)
- **Total Story Points:** 186 Points
- **Status:** **DONE** (Implemented, Verified, and Deployed)

---

## 5. Phase-to-Jira Traceability Matrix (Phases 1–24)

| Project Phase | Phase Name | Primary Epic | User Stories | Status |
|:---|:---|:---|:---|:---:|
| **Phase 1** | Requirements & Threat Modeling | EPIC-9, EPIC-10 | US-34, US-35, US-36, US-39 | Done |
| **Phase 2** | Database Layer (PostgreSQL 16) | EPIC-1 | US-06 | Done |
| **Phase 3** | Digital Twin Graph (NetworkX) | EPIC-2 | US-07 | Done |
| **Phase 4** | Telemetry Normalizer & Validation | EPIC-1 | US-01, US-02 | Done |
| **Phase 5** | REST Ingestion Pipeline | EPIC-1 | US-01, US-02 | Done |
| **Phase 6** | Mosquitto MQTT Bridge | EPIC-1 | US-03 | Done |
| **Phase 7** | Incident Correlation Engine | EPIC-3 | US-14 | Done |
| **Phase 8** | Live State & Drift Auto-Reconcile | EPIC-2 | US-08, US-09 | Done |
| **Phase 9** | Time-Travel Snapshots (Full + Delta)| EPIC-2 | US-10 | Done |
| **Phase 10**| Rule Anomaly Detection (`RULE-001..010`) | EPIC-3 | US-12 | Done |
| **Phase 11**| Asset State Machines (9 Types) | EPIC-3 | US-13 | Done |
| **Phase 12**| Dynamic 6-Component Risk Scoring | EPIC-3 | US-15 | Done |
| **Phase 13**| End-to-End Orchestrator (`SIM-01..03`) | EPIC-5, EPIC-6 | US-20, US-25 | Done |
| **Phase 14**| Attack Story & MITRE ATT&CK Mapping | EPIC-5 | US-20 | Done |
| **Phase 15**| Automated IOC Extraction (11 Types) | EPIC-4 | US-16 | Done |
| **Phase 16**| Threat Intel Enrichment (VT/Abuse/OTX) | EPIC-4 | US-17 | Done |
| **Phase 17**| BFS Topology Blast Radius Model | EPIC-5 | US-19 | Done |
| **Phase 18**| Automated Triage Classifier ($F_1=0.94$) | EPIC-5 | US-21 | Done |
| **Phase 19**| Flask Live Fleet Dashboard & Map | EPIC-6 | US-23, US-24, US-25, US-26 | Done |
| **Phase 20**| Eclipse Ditto Digital Twin Integration | EPIC-2 | US-11 | Done |
| **Phase 21**| Test Automation (~200 Tests, $\ge 85\%$) | EPIC-10 | US-37 | Done |
| **Phase 22**| Unsupervised ML Models + SHAP XAI | EPIC-7, EPIC-5 | US-27, US-28, US-29, US-22 | Done |
| **Phase 23**| Dockerization (14 Containers) & CI/CD | EPIC-8 | US-30, US-31, US-32 | Done |
| **Phase 24**| AWS Terraform Cloud IaC Deployment | EPIC-8 | US-33 | Done |
| **Contribution C8** | Threat-Intel Risk Reweighting | EPIC-4 | US-18 | Done |

---

## 6. How to Import into Jira Cloud

### Option 1: One-Click CSV Import (Recommended)
1. Navigate to **Jira Settings** (`⚙`) → **System** → **External System Import**.
2. Select **CSV**.
3. Upload [`docs/jira_import_sscdt.csv`](jira_import_sscdt.csv).
4. Select Project: **Smart Supply Chain Cyber Digital Twin (`SSCDT`)**.
5. Map fields automatically:
   - `Issue Type` → `Issue Type`
   - `Summary` → `Summary`
   - `Description` → `Description`
   - `Acceptance Criteria` → `Environment` or append to `Description`
   - `Epic Name` → `Epic Name`
   - `Epic Link` → `Epic Link`
   - `Story Points` → `Story Points`
   - `Component/s` → `Component/s`
   - `Labels` → `Labels`
   - `Priority` → `Priority`
   - `Sprint` → `Sprint`
6. Click **Begin Import**. All 10 Epics and 39 User Stories will be created and linked.

### Option 2: Programmatic Setup via Python Script
Run the automated initialization script located at [`scripts/setup_jira.py`](../scripts/setup_jira.py):
```bash
# Generate API token at: https://id.atlassian.com/manage-profile/security/api-tokens
python scripts/setup_jira.py \
  --url "https://mastersudhan1234.atlassian.net" \
  --email "your-email@domain.com" \
  --token "YOUR_JIRA_API_TOKEN"
```

---

## 7. Jira Scrum Reports to Review

Enable the following standard Jira Agile reports in board settings:
1. **Sprint Burndown Chart**: Track daily point burn across Sprint 1 (143 pts) and Sprint 2 (186 pts).
2. **Velocity Chart**: Measure team commitment vs completion across sprints.
3. **Cumulative Flow Diagram (CFD)**: Monitor work-in-progress (WIP) and detect queue bottlenecks.
4. **Epic Report**: Visualize completion percentage across all 10 core system epics.
5. **Version Report**: Track milestone delivery (Phase-I vs Phase-II).
6. **Created vs. Resolved Issues Report**: Demonstrate backlog health and resolution velocity.
7. **Component Breakdown Pie Chart**: Verify balanced distribution across all 10 architectural components.
8. **Control Chart**: Analyze lead time and cycle time for bug fixes and feature implementation.
