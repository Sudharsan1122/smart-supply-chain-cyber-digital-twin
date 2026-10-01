# Phase 1 – Requirement Engineering

## Project Details
- **Project Title:** Smart Supply Chain Cyber Digital Twin
- **Course:** 20CYS495 Project Phase-I
- **Team Members:** Sudharsan S, Manojkumar A
- **Repository:** [GitHub: Sudharsan1122/smart-supply-chain-cyber-digital-twin](https://github.com/Sudharsan1122/smart-supply-chain-cyber-digital-twin)

---

## Exercise 1: Identify Requirements

### System Objective

To develop a secure Cyber Digital Twin for a 32-asset supply chain that ingests real-time telemetry via REST and MQTT, detects anomalies using rule-based + ML engines, enriches Indicators of Compromise (IOCs) against live threat intelligence, reconstructs attacks as MITRE-mapped stories, computes blast radius through topology traversal, and auto-triages every detection with measurable precision, recall, and F1.

### Stakeholders

- **Security Analyst**: Monitors operational twin state, investigates reconstructed attack stories, reviews blast radii, and inspects threat intelligence IOCs.
- **SOC Operator**: Monitors live alert feeds, inspects automated triage metrics (confusion matrix, precision/recall/F1), and triggers containment workflows.
- **System Administrator**: Manages system credentials, API keys, service lifecycle, container orchestration, and health/readiness endpoints.
- **Attacker (Simulated)**: Automated adversary agent executing multi-stage attack scenarios (`SIM-01` telematics compromise, `SIM-02` warehouse IoT sabotage, `SIM-03` credential anomaly).
- **External Systems**: 
  - Wazuh SIEM (Host-based IDS & compliance monitoring)
  - Suricata IDS (Network intrusion detection & protocol inspection)
  - Eclipse Ditto (Standardized digital twin thing/feature repository)
  - VirusTotal (Reputation analysis for domains, IPs, and file hashes)
  - AbuseIPDB (IP address abuse confidence scoring)
  - AlienVault OTX (Crowdsourced threat pulses and adversary IOCs)

---

### Functional Requirements (23)

| ID | Requirement |
|:---|:---|
| **FR1** | Ingest telemetry via REST API (`POST /api/telemetry`) |
| **FR2** | Ingest telemetry via MQTT (`supply_chain/telemetry/+`) |
| **FR3** | Ingest security events via REST (`POST /api/events`) |
| **FR4** | Pull alerts from Wazuh SIEM |
| **FR5** | Read alerts from Suricata IDS |
| **FR6** | Validate all incoming payloads via Pydantic v2 |
| **FR7** | Normalize payloads into metric rows + twin state |
| **FR8** | Persist telemetry, events, and detections in PostgreSQL |
| **FR9** | Maintain live digital twin graph (32 assets, NetworkX) |
| **FR10** | Detect anomalies using 10 rule-based rules |
| **FR11** | Detect anomalies using ML (Isolation Forest + One-Class SVM) |
| **FR12** | Correlate multi-source signals into incidents |
| **FR13** | Extract 11 IOC types from every payload |
| **FR14** | Enrich IOCs against VirusTotal, AbuseIPDB, AlienVault OTX |
| **FR15** | Reweight asset risk scores based on IOC verdicts (C8) |
| **FR16** | Compute blast radius via topology traversal |
| **FR17** | Reconstruct attacks as MITRE-mapped stories |
| **FR18** | Auto-triage detections as TP/FP/FN/TN |
| **FR19** | Simulate 3 attack scenarios (SIM-01, SIM-02, SIM-03) |
| **FR20** | Display live dashboard with 4 tabs + geographic map |
| **FR21** | Sync twin state to Eclipse Ditto every 5 seconds |
| **FR22** | Provide XAI (SHAP) for every ML detection |
| **FR23** | Generate one-command end-to-end demo |

---

### Non-Functional Requirements (10)

| ID | Requirement | Target |
|:---|:---|:---|
| **NFR1** | Performance | Ingestion to detection < 2 seconds |
| **NFR2** | Availability | 99% uptime for API + dashboard |
| **NFR3** | Reliability | Graceful degradation on external API failure |
| **NFR4** | Scalability | Handle 32 assets now, 500+ in Phase-III |
| **NFR5** | Usability | Dashboard updates every 3 seconds |
| **NFR6** | Maintainability | ≥85% test coverage, zero cyclic dependencies |
| **NFR7** | Observability | Structured logs + health/readiness probes |
| **NFR8** | Portability | Runs on Docker (Windows / Linux / macOS) |
| **NFR9** | Interoperability | REST + MQTT + Eclipse Ditto compatible |
| **NFR10** | Reproducibility | One-command setup via Docker Compose |

---

### Security Requirements (20)

| ID | Requirement | Implementation |
|:---|:---|:---|
| **SR1** | Secure authentication | JWT bearer tokens (Wazuh API) |
| **SR2** | Password hashing | bcrypt via passlib |
| **SR3** | Role-based access control | Analyst / SOC / Admin roles |
| **SR4** | Asset data protection | Pydantic validation + encryption at rest |
| **SR5** | Telemetry integrity | HTTPS/TLS + Pydantic validation |
| **SR6** | IOC integrity | Allowlist filter (private IPs rejected) |
| **SR7** | HTTPS / TLS | TLS 1.2+ on all external API calls |
| **SR8** | Input validation | Pydantic v2 strict mode + custom validators |
| **SR9** | Secure session management | Timezone-aware tokens with expiry |
| **SR10** | Security logging | Structured JSON logs + audit trail |
| **SR11** | SSRF protection | Domain allowlist for outbound calls |
| **SR12** | IOC allowlist filter | Private/reserved IPs excluded |
| **SR13** | Non-root containers | Docker USER app in all images |
| **SR14** | Secrets management | .env + AWS Secrets Manager |
| **SR15** | Rate limiting | Token bucket per external provider |
| **SR16** | No eval/exec/pickle | Static code review + SonarQube |
| **SR17** | Dependency scanning | Bandit + pip-audit + safety |
| **SR18** | Container isolation | Separate Docker networks |
| **SR19** | Health checks | /api/health + /api/ready probes |
| **SR20** | XAI explainability | SHAP values for every ML detection |

---

### Deliverable: Software Requirements Specification (SRS)

**Summary:** 23 Functional + 10 Non-Functional + 20 Security = **53 requirements**.

#### Requirement Groups at a Glance

| Group | IDs | Purpose |
|:---|:---|:---|
| **Ingestion** | FR1–FR5 | Accept data from all sources (REST, MQTT, Wazuh SIEM, Suricata IDS) |
| **Processing** | FR6–FR9 | Validate, normalize, persist, and model cyber-physical state |
| **Detection** | FR10–FR12 | Hybrid rule-based checks + unsupervised ML + incident correlation |
| **Intelligence** | FR13–FR15 | IOC extraction + live reputation enrichment + dynamic risk reweighting (C8) |
| **Analysis** | FR16–FR18 | Dependency blast radius + MITRE attack stories + automated triage |
| **Operations** | FR19–FR23 | Attack simulation + Flask dashboard + Ditto sync + SHAP XAI + demo |
| **Performance** | NFR1–NFR5 | Sub-second latency, 99% availability, graceful degradation, and responsiveness |
| **Quality** | NFR6–NFR10 | ≥85% test coverage, structured logging, multi-platform Docker portability |
| **Security** | SR1–SR20 | 20-layer defense-in-depth architecture covering CIA and STRIDE vectors |
