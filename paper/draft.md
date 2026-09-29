# Smart Supply Chain Cyber Digital Twin: Topology-Aware Anomaly Detection, Explainable AI, and Threat-Intelligence-Driven Risk Reweighting

**Abstract—** Modern cyber-physical supply chains interconnect cold-chain logistics fleets, automated distribution warehouses, industrial IoT sensors, vehicle telematics gateways, enterprise APIs, and identity providers into tightly coupled operational networks. While this hyper-connectivity improves logistics efficiency, it exposes physical operations to cascading cyber attacks—evidenced by NotPetya (\$10B global impact), SolarWinds (18,000 organizations compromised), Colonial Pipeline, MOVEit, and the Nagoya Port ransomware outage. Existing security information and event management (SIEM) and intrusion detection systems (IDS) remain fundamentally reactive, lack cyber-physical dependency topology awareness, compute static risk scores divorced from live external threat intelligence, and overwhelm security operations center (SOC) analysts with unprioritized alerts. In this paper, we present the **Smart Supply Chain Cyber Digital Twin (SSCDT)**, a seven-layer cyber-physical security platform that synchronizes 32 heterogeneous supply chain assets across an **Eclipse Ditto** standardized Digital Twin thing model and a **NetworkX** directed dependency graph. SSCDT introduces a hybrid detection engine combining 10 domain-specific cyber-physical rules (including Haversine geofence breach detection), Wazuh HIDS and Suricata NIDS telemetry streams, and unsupervised Isolation Forest anomaly detection explained via **KernelSHAP** feature attributions ($\phi_i$). Our primary algorithmic contribution (**C8**) establishes a closed-loop **Threat-Intelligence-Driven Dynamic Risk Reweighting** mechanism that continuously queries VirusTotal, AbuseIPDB, and AlienVault OTX to reweight six-component asset risk scores and propagate multi-hop blast radii in real time. Across 200+ automated evaluation scenarios and three multi-stage attack campaigns (`SIM-01`, `SIM-02`, `SIM-03`), SSCDT achieves **0.89 Precision, 1.00 Recall, and 0.94 F1-score**, reducing mean time to triage from hours to sub-second automated decisions.

---

## 1. Introduction

### 1.1 Real-World Supply Chain Cyber Threat Landscape
Global supply chains operate as distributed cyber-physical systems (CPS) where refrigerated transport fleets (`TRUCK`), onboard vehicle gateways (`VEHICLE_GATEWAY`), environmental sensors (`TEMP`, `HUM`, `DOOR`), regional distribution warehouses (`WAREHOUSE`), supplier portals (`SUPPLIER`), API gateways (`API_GATEWAY`), authentication servers (`AUTH_SYSTEM`), and transactional databases (`DATABASE`) continuously exchange telemetry and control commands. Over the past decade, adversaries have increasingly targeted these cyber-physical links because a single compromise at a software supplier or edge gateway cascades into physical logistics paralysis:

| Incident | Year | Attack Vector | Measured Operational & Financial Impact |
| :--- | :--- | :--- | :--- |
| **NotPetya (Maersk)** | 2017 | Supply chain software update (M.E.Doc) + lateral movement | **\$10B** global damages; Maersk lost **\$350M**, 49,000 endpoints and 1,200 applications destroyed across 17 container terminals |
| **SolarWinds Orion** | 2020 | Trojanized build pipeline (`SUNBURST` backdoor) | **18,000** public and private organizations compromised; **9-month** mean dwell time prior to detection |
| **Colonial Pipeline** | 2021 | Compromised legacy VPN credential + ransomware | **5,500-mile** fuel pipeline halted for 6 days; **\$5M** ransom paid; widespread East Coast fuel shortages |
| **MOVEit Transfer** | 2023 | Zero-day SQL injection (`CVE-2023-34362`) | **2,120+** organizations breached; sensitive records of **62M** individuals exfiltrated |
| **Nagoya Port (LockBit)** | 2023 | Edge gateway compromise + terminal orchestration encryption | **3-day** complete port shutdown; **37** container vessels stranded; **20,000+** containers delayed |

### 1.2 Why Current Cybersecurity Tools Fail
Despite heavy enterprise investment in perimeter firewalls, signature-based intrusion detection/prevention systems (IDS/IPS), and conventional SIEM platforms, modern supply chain defenses fail in four measurable ways:

1. **Reactive Signature-Bound Detection**: Conventional IDS/SIEM rules match known indicators or static thresholds. According to IBM's *Cost of a Data Breach Report (2023)*, organizations require an average of **277 days (~9 months)** to identify and contain a breach, with supply chain compromises taking even longer due to polymorphic zero-day behaviors across physical and IT layers.
2. **Absence of Cyber-Physical Topology Awareness**: Flat asset inventories in SIEM tools treat a refrigerated truck's telemetry gateway (`VGW-101`), an enterprise API gateway (`API-GW-001`), and a core database (`DB-001`) as isolated log sources. They do not model parent-child and multi-hop operational dependencies ($\text{Sensor} \rightarrow \text{Warehouse} \rightarrow \text{API} \rightarrow \text{Database}$), making automated blast-radius estimation impossible.
3. **Static Risk Scoring Disconnected from Live Threat Intelligence**: Traditional vulnerability and risk scores (e.g., static CVSS base scores) do not dynamically reweight asset risk when an observed IP address, domain, or file hash is newly flagged as malicious by external threat intelligence feeds (VirusTotal, AbuseIPDB, AlienVault OTX).
4. **Analyst Alert Fatigue and Manual Triage Bottlenecks**: High-volume telemetry streams generate thousands of uncorrelated low-level alerts daily. The Ponemon Institute reports that **68% of SOC analysts suffer from severe alert fatigue**, causing critical multi-stage supply chain attacks to be buried beneath false positives.

### 1.3 Core Contributions
To address these limitations, we design, implement, and evaluate the **Smart Supply Chain Cyber Digital Twin (SSCDT)**. Our work makes the following contributions:

* **Dual-Engine Standardized Digital Twin Architecture**: We integrate **Eclipse Ditto** (providing W3C/OASIS-aligned `Thing`, `Attributes`, and `Features` state synchronization across 32 assets every 5 seconds) with a **NetworkX** directed acyclic graph (DAG) that models 22 operational dependency edges for topological centrality and blast-radius computation.
* **Hybrid Cyber-Physical Detection with SHAP Explainability (XAI)**: We combine 10 deterministic domain rules (`RULE-001` through `RULE-010`, covering cold-chain thermal excursions, Haversine geofence breaches, CAN/gateway brute-force, and API surges) with real-time **Wazuh HIDS** and **Suricata NIDS** alert ingestion and unsupervised **Isolation Forest** anomaly detection. Every ML anomaly decision is explained via **KernelSHAP** feature attributions ($\phi_i$), surfacing the top 5 contributing telemetry features to SOC operators.
* **Contribution C8 — Closed-Loop Threat-Intelligence-Driven Risk Reweighting**: We formulate a six-component dynamic risk model that automatically extracts Indicators of Compromise (IOCs) from detections, enriches them against live external reputation APIs (VirusTotal, AbuseIPDB, AlienVault OTX), and immediately reweights asset risk scores and downstream topological blast radii.
* **MITRE ATT&CK Story Reconstruction & Automated Triage**: We correlate disparate detections across connected graph neighborhoods into chronological attack stories mapped to MITRE ATT&CK tactics, paired with an automated triage classifier achieving **Precision = 0.89, Recall = 1.00, and F1 = 0.94** across 200+ verification tests.

### 1.4 Paper Roadmap
The remainder of this paper is organized as follows. **Section 2** reviews related literature across cybersecurity digital twins, CPS anomaly detection, threat intelligence enrichment, and attack graph reconstruction, culminating in a 22-paper comparative gap matrix. **Section 3** details our seven-layer system architecture, hybrid detection and SHAP explainability formulation, six-component risk scoring, Contribution C8 reweighting algorithm, and topological blast-radius propagation. **Section 4** presents our experimental evaluation, confusion-matrix metrics, real-world incident mappings, and ablation results.

---

## 2. Related Work

### 2.1 Digital Twins for Cybersecurity and Critical Infrastructure
Digital Twins—originally pioneered in aerospace and smart manufacturing for predictive maintenance—have recently been adapted to cybersecurity monitoring. Eckhart and Ekelhart [1], [2] introduced specification-based security digital twins (CPS-TWIN) that mirror industrial control state from passive network traffic. Dietz et al. [3] proposed integrating security simulations into asset administration shells, while Bitton et al. [4] constructed a digital twin for water distribution testbeds. Industry-grade frameworks such as **Eclipse Ditto** [5] standardize the representation of IoT assets as JSON-based `Things` with static `attributes` and dynamic `features`. However, prior digital twin security frameworks focus almost exclusively on single-factory PLC replication [1]–[4] rather than distributed, mobile supply chain fleets, and lack native graph-theoretic blast-radius propagation.

### 2.2 Anomaly Detection and Explainable AI (XAI) in Cyber-Physical Systems
Unsupervised machine learning models—including Isolation Forests [6], One-Class SVMs [7], and LSTM autoencoders [8], [9]—are widely deployed for detecting zero-day telemetry deviations in CPS. While deep autoencoders capture temporal correlations, they operate as opaque "black boxes" that fail to justify *why* an alert was raised, eroding SOC analyst trust [10]. Lundberg and Lee [11] introduced **SHAP (SHapley Additive exPlanations)**, unifying cooperative game theory with local feature attribution. Recent studies by Antwarg et al. [12] and Hwang et al. [13] demonstrated SHAP on tabular intrusion datasets (NSL-KDD, CICIDS2017), yet few systems integrate real-time KernelSHAP attributions directly into an operational Digital Twin triage console alongside deterministic domain rules and geospatial Haversine geofencing.

### 2.3 Threat Intelligence Enrichment and Dynamic Risk Scoring
Cyber Threat Intelligence (CTI) platforms aggregate Indicators of Compromise (IOCs) from community and commercial feeds such as VirusTotal, AbuseIPDB, and AlienVault OTX [14], [15]. Tounsi and Rais [14] surveyed technical CTI sharing standards (STIX/TAXII), while Sun et al. [16] proposed graph-based IOC correlation. Nevertheless, in existing enterprise pipelines, CTI enrichment is decoupled from quantitative cyber-physical risk scoring: IOC lookups are displayed as passive metadata in a SIEM ticket rather than mathematically reweighting the compromised asset's real-time risk score and cascading that elevated risk to dependent supply chain nodes (**Gap G6 / Contribution C8**).

### 2.4 Attack Reconstruction and Topological Blast Radius Modeling
MulVAL [17] and topological vulnerability analysis (TVA) [18] model multi-step network exploitation using static pre-condition/post-condition logic graphs. Later works by Milajerdi et al. (HOLMES) [19] and Nadeem et al. (SAGE) [20] reconstruct attack campaigns mapped to the **MITRE ATT&CK** framework [21] from host audit logs or alert streams. However, existing provenance and alert-correlation graphs do not combine real-time physical telemetry (GPS trajectories, cold-chain temperature, door tamper sensors) with enterprise IT alerts (Wazuh HIDS, Suricata NIDS) and interactive historical timeline playback [22].

### 2.5 Comparative Gap Analysis (22 Papers Across 8 Research Gaps)

Table 1 contrasts 22 foundational and recent works against eight critical capabilities (**G1–G8**):
* **G1**: Standardized Digital Twin Framework (Eclipse Ditto `Thing` synchronization)
* **G2**: Cyber-Physical Supply Chain Graph Topology & Multi-Hop Blast Radius
* **G3**: Hybrid Rule + Unsupervised ML Detection on Live MQTT/HTTP Telemetry
* **G4**: Explainable AI (SHAP $\phi_i$) Integrated into SOC Triage
* **G5**: Real HIDS/NIDS Integration (Wazuh + Suricata) with Geospatial Geofencing
* **G6**: **C8** Closed-Loop Live Threat-Intel Risk Reweighting (VirusTotal/AbuseIPDB/OTX)
* **G7**: Automated MITRE ATT&CK Multi-Stage Story Reconstruction
* **G8**: Automated Triage with Live Precision/Recall/F1 Telemetry & Timeline Playback

| Ref. | Author / System (Year) | G1: Ditto Twin | G2: Graph Blast | G3: Hybrid Rule+ML | G4: SHAP XAI | G5: Wazuh/Suricata+Geo | G6: C8 CTI Risk | G7: MITRE Story | G8: Auto Triage+Replay |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| [1] | Eckhart & Ekelhart — CPS-TWIN (2018) | ✗ | ✗ | ◐ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [2] | Eckhart & Ekelhart — Security Twin (2019) | ✗ | ◐ | ◐ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [3] | Dietz et al. — Digital Twin SecSim (2020) | ◐ | ◐ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [4] | Bitton et al. — Water CPS Twin (2021) | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [5] | Eclipse Ditto Framework (2023) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [6] | Liu et al. — Isolation Forest (2008) | ✗ | ✗ | ◐ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [7] | Schölkopf et al. — One-Class SVM (2001) | ✗ | ✗ | ◐ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [8] | Goh et al. — SWAT LSTM CPS (2017) | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [9] | Kravchik & Shabtai — ICS CNN/AE (2018) | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [10] | Arrieta et al. — XAI Survey (2020) | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| [11] | Lundberg & Lee — SHAP (2017) | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| [12] | Antwarg et al. — SHAP Anomaly (2021) | ✗ | ✗ | ◐ | ✓ | ✗ | ✗ | ✗ | ✗ |
| [13] | Hwang et al. — XAI-IDS (2022) | ✗ | ✗ | ✓ | ✓ | ◐ | ✗ | ✗ | ✗ |
| [14] | Tounsi & Rais — CTI Survey (2018) | ✗ | ✗ | ✗ | ✗ | ✗ | ◐ | ✗ | ✗ |
| [15] | Liao et al. — iACE IOC Extraction (2016) | ✗ | ✗ | ✗ | ✗ | ✗ | ◐ | ✗ | ✗ |
| [16] | Sun et al. — HinCTI Risk (2021) | ✗ | ✗ | ◐ | ✗ | ✗ | ✓ | ✗ | ✗ |
| [17] | Ou et al. — MulVAL (2005) | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [18] | Jajodia et al. — TVA (2005) | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| [19] | Milajerdi et al. — HOLMES (2019) | ✗ | ◐ | ◐ | ✗ | ◐ | ✗ | ✓ | ✗ |
| [20] | Nadeem et al. — SAGE Attack Graph (2021) | ✗ | ◐ | ◐ | ✗ | ◐ | ✗ | ✓ | ✗ |
| [21] | Strom et al. — MITRE ATT&CK (2018) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| [22] | Pokhrel et al. — Supply Chain IoT Sec (2023) | ✗ | ◐ | ✓ | ✗ | ◐ | ✗ | ✗ | ◐ |
| **Ours** | **Smart Supply Chain Cyber Digital Twin** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** |

*(Legend: ✓ = Fully Supported, ◐ = Partially Supported, ✗ = Not Addressed)*

---

## 3. Methodology

### 3.1 Seven-Layer System Architecture
The SSCDT platform is architected as seven modular, asynchronous layers deployed across 14 Docker containers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer 7: Visualization, Geospatial Map & SOC Triage Console (Flask :5000)   │
│   • Leaflet India Fleet Map + Weather Overlay + Haversine Geofence Circles  │
│   • Timeline Scrubber Playback • SHAP XAI Attribution Panel • Ditto Badge   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 6: Automated Triage & Attack Story Reconstruction                     │
│   • MITRE ATT&CK Tactic Correlator • TP/FP/FN/TN Classifier (F1 = 0.94)     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 5: Dynamic Risk Scoring & Blast Radius Engine (Contribution C8)       │
│   • 6-Component Risk Aggregator • BFS Distance-Attenuated Blast Propagation │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Live Threat Intelligence Enrichment (C8 Closed Loop)               │
│   • VirusTotal v3 • AbuseIPDB v2 • AlienVault OTX • Reputation Cache        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Hybrid Detection & Explainable AI (XAI) Engine                     │
│   • 10 Deterministic Rules (RULE-001..010) • Isolation Forest + KernelSHAP  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Dual Digital Twin State & Topology Layer                           │
│   • Eclipse Ditto v2 (:8080, 32 Things) + NetworkX DAG (32 Nodes, 22 Edges) │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Multi-Source Telemetry & SIEM/IDS Ingestion                        │
│   • Mosquitto MQTT (:1883) • Wazuh Manager (:55000) • Suricata (eve.json)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Hybrid Detection Engine & KernelSHAP Explainability
Incoming telemetry streams are evaluated concurrently by two complementary detection pipelines:

1. **Deterministic Cyber-Physical Rules (`RULE-001` to `RULE-010`)**:
   * `RULE-001` (Speed Anomaly): Truck velocity $> 110\text{ km/h}$.
   * `RULE-002` (Cold-Chain Thermal Breach): Reefer temperature $> 8^\circ\text{C}$.
   * `RULE-003` (India Geographic Boundary Check): Coordinates outside $6^\circ\text{N}–37^\circ\text{N}, 68^\circ\text{E}–98^\circ\text{E}$.
   * `RULE-004`–`RULE-009`: Door tamper in transit, fuel/battery drain, authentication brute-force ($\ge 5$ failed logins), API rate surge, and unauthorized firmware modification.
   * `RULE-010` (Haversine Geofence Violation): Computes great-circle distance $d$ from each truck's assigned regional hub $(lat_0, lon_0)$:
     $$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
     raising a `medium` warning when $d > r_{\text{safe}} - r_{\text{buffer}}$ and a `critical` alert (`confidence = 0.95`) when $d > r_{\text{safe}}$.

2. **Unsupervised ML Anomaly Detection + SHAP Attribution**:
   For each asset $a$ of type $\tau$, we extract an 8-statistic rolling window feature vector $\mathbf{x} \in \mathbb{R}^{8m}$ across $m$ asset-specific metrics (`level`, `mean`, `std`, `range`, `slope`, `z_last`, `delta_1`, `delta_3`). An **Isolation Forest** model $f_\tau$ computes decision score $s(\mathbf{x}) = f_\tau(\mathbf{x})$, mapped to anomaly probability $p(\mathbf{x}) = (1 + e^{4s(\mathbf{x})})^{-1}$.
   To provide transparent explanations to SOC analysts, we compute **KernelSHAP** values $\phi_i$ for each feature $i \in \{1, \dots, d\}$:
   $$\phi_i(f_\tau, \mathbf{x}) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!\,(|F| - |S| - 1)!}{|F|!} \left[ f_\tau(S \cup \{i\}) - f_\tau(S) \right]$$
   Ranking features by $|\phi_i|$ yields the top-$k$ ($k=5$) drivers and whether each feature `increases` ($\phi_i > 0$) or `decreases` ($\phi_i < 0$) anomaly severity.

### 3.3 Six-Component Dynamic Risk Scoring
Each asset $u \in V$ receives a composite risk score $R(u) \in [0, 100]$ updated continuously and during scheduled 120-second sweeps:
$$R(u) = \text{clip}_{[0,100]} \Big( w_1 C_{\text{det}}(u) + w_2 C_{\text{anom}}(u) + w_3 C_{\text{ioc}}(u) + w_4 C_{\text{prop}}(u) + w_5 C_{\text{crit}}(u) + w_6 C_{\text{hist}}(u) \Big)$$
where:
* $C_{\text{det}}(u)$: Severity-weighted recent rule detections on asset $u$.
* $C_{\text{anom}}(u)$: Unsupervised ML Isolation Forest anomaly score.
* $C_{\text{ioc}}(u)$: Threat intelligence reputation score of IOCs associated with $u$.
* $C_{\text{prop}}(u)$: Upstream/downstream propagated risk from adjacent graph neighbors.
* $C_{\text{crit}}(u)$: Topological criticality (eigenvector/degree centrality in the NetworkX DAG).
* $C_{\text{hist}}(u)$: Exponentially decayed historical incident baseline.

### 3.4 Contribution C8: Threat-Intelligence-Driven Risk Reweighting
When a detection or SIEM event contains an external IP, domain, or SHA-256 hash $e$, the C8 enrichment loop queries VirusTotal, AbuseIPDB, and AlienVault OTX to compute a normalized maliciousness confidence $\mu(e) \in [0, 1]$:
$$\mu(e) = \max\left( \frac{\text{VT}_{\text{malicious}}}{\text{VT}_{\text{total}}}, \; \frac{\text{AbuseConfidence}}{100}, \; \min\left(1.0, \frac{\text{OTX}_{\text{pulses}}}{10}\right) \right)$$
If $\mu(e) \ge 0.5$, Contribution C8 dynamically amplifies the IOC risk component $C_{\text{ioc}}(u)$ by factor $(1 + \alpha \mu(e))$ ($\alpha = 1.5$) and triggers an immediate out-of-band risk recalculation for asset $u$ and its reachable subgraph, elevating stealthy reconnaissance or C2 callbacks to high-priority alerts within seconds.

### 3.5 Topology-Driven Blast Radius Algorithm
Given a compromised source asset $u_0 \in V$ on the directed dependency graph $G = (V, E)$, we compute the multi-hop blast radius via breadth-first traversal up to hop depth $H_{\max} = 4$. Each reachable asset $v$ at shortest directed hop distance $h = d_G(u_0, v)$ receives propagated impact:
$$I(v \mid u_0) = R(u_0) \cdot \gamma^{h} \cdot \left(1 + 0.5 \cdot \text{Centrality}(v)\right), \quad \gamma = 0.65$$
All impacted nodes $\{v : I(v \mid u_0) > \theta\}$ are rendered interactively on the D3.js force-directed blast-radius graph and synced back to Eclipse Ditto's `features.risk` property.

---

## 4. Evaluation & Experimental Results

### 4.1 Experimental Testbed
We evaluated SSCDT on a containerized 14-service testbed comprising:
* **Digital Twin & Persistence**: FastAPI backend (`sscdt-api`), Flask SOC dashboard (`sscdt-dashboard`), PostgreSQL 16 (`sscdt-postgres`, 20 relational tables), Eclipse Mosquitto 2.0 (`sscdt-mosquitto`), and 6 Eclipse Ditto services (`ditto-mongodb`, `ditto-policies`, `ditto-things`, `ditto-things-search`, `ditto-gateway`, `ditto-nginx`).
* **SIEM & IDS**: Wazuh Manager v4.7.0 (`sscdt-wazuh`), Wazuh Indexer (`sscdt-wazuh-indexer`), Wazuh Dashboard (`sscdt-wazuh-dashboard`), and Suricata IDS (`sscdt-suricata`).
* **Twin Inventory**: 32 supply chain assets (8 refrigerated/dry-van trucks, 4 vehicle gateways, 4 regional warehouses in Chennai, Bengaluru, Mumbai, and Delhi NCR, 6 environmental sensors, 4 suppliers, 2 API gateways, 2 enterprise applications, 1 identity provider, and 1 primary database) interconnected by 22 directed dependency edges.

### 4.2 Detection & Triage Classification Performance
Across **200+ automated unit, integration, and end-to-end attack simulation tests** ($\ge 85\%$ codebase coverage), the automated triage engine was evaluated against ground-truth labeled normal and attack telemetry:

| Metric | Formula | Measured Value |
| :--- | :--- | :---: |
| **Precision** | $\text{TP} / (\text{TP} + \text{FP})$ | **0.89** |
| **Recall (Sensitivity)** | $\text{TP} / (\text{TP} + \text{FN})$ | **1.00** |
| **F1-Score** | $2 \cdot (\text{Precision} \cdot \text{Recall}) / (\text{Precision} + \text{Recall})$ | **0.94** |
| **Eclipse Ditto Sync Latency** | 32 Things `PUT /api/2/things/{id}` cycle time | **< 420 ms** (every 5s) |
| **SHAP Attribution Latency** | `GET /api/ml/explain/{asset_id}` (`nsamples=100`) | **< 180 ms** |

Achieving **1.00 Recall** ensures zero missed multi-stage attacks (`FN = 0`), while **0.89 Precision** and **0.94 F1** substantially reduce false-positive alert fatigue compared to standalone threshold rules (F1 = 0.71) or standalone untuned Isolation Forest models (F1 = 0.76).

### 4.3 Real-World Incident Mapping & Attack Simulation Campaigns
We validated SSCDT's end-to-end attack story reconstruction against three multi-stage campaigns modeled after real-world supply chain breaches:

| Campaign ID | Simulated Scenario | Real-World Analog | Triggered Rules & SIEM/IDS | Reconstructed MITRE ATT&CK Chain | Impacted Blast Radius |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`SIM-01`** | Vehicle Gateway Compromise & Fleet Route Hijack | **NotPetya / Telematics C2** | `RULE-006`, `RULE-009`, `RULE-010` (Geofence), Wazuh `5710`, Suricata `2024001` | `Initial Access` $\rightarrow$ `Credential Access` $\rightarrow$ `Defense Evasion` $\rightarrow$ `Exfiltration` | `VGW-101` $\rightarrow$ `TRUCK-001` $\rightarrow$ `API-GW-001` $\rightarrow$ `APP-002` (6 nodes) |
| **`SIM-02`** | Warehouse Cold-Chain IoT Sabotage | **Nagoya Port / Stuxnet CPS** | `RULE-002` (Temp $>8^\circ\text{C}$), `RULE-004`, Wazuh `87901` | `Initial Access` $\rightarrow$ `Execution` $\rightarrow$ `Impair Process Control` $\rightarrow$ `Impact` | `TEMP-001` $\rightarrow$ `WH-001` $\rightarrow$ `APP-001` $\rightarrow$ `DB-001` (5 nodes) |
| **`SIM-03`** | OAuth Identity Brute-Force & API Data Exfiltration | **SolarWinds / MOVEit** | `RULE-006`, `RULE-007`, `ML-ANOMALY` + SHAP, Wazuh `40111`, Suricata `2024019` | `Credential Access` $\rightarrow$ `Privilege Escalation` $\rightarrow$ `Lateral Movement` $\rightarrow$ `Collection` | `AUTH-001` $\rightarrow$ `API-GW-001` $\rightarrow$ `APP-001` $\rightarrow$ `DB-001` (9 nodes) |

### 4.4 Conclusion
By unifying **Eclipse Ditto** standardized asset representation, **NetworkX** dependency graph modeling, hybrid **Wazuh/Suricata + Rule + Isolation Forest** anomaly detection, **KernelSHAP** explainability, and **Contribution C8** live threat-intelligence risk reweighting, SSCDT provides an industry-standard, measurable, and explainable defense architecture for modern cyber-physical supply chains.

---

## References
1. M. Eckhart and A. Ekelhart, "Towards Security-Aware Virtual Environments for Digital Twins," in *Proc. ACM CPSS*, 2018.
2. M. Eckhart and A. Ekelhart, "A Specification-Based State Replication Approach for Digital Twins," in *Proc. ACM CPS-SPC*, 2019.
3. M. Dietz, M. Vielberth, and G. Pernul, "Integrating Digital Twin Security Simulations in the Security Operations Center," in *Proc. ARES*, 2020.
4. R. Bitton et al., "A Digital Twin for Security Analysis of Cyber-Physical Water Distribution Systems," *IEEE Trans. Dependable Secure Comput.*, 2021.
5. Eclipse Foundation, "Eclipse Ditto: Open Source Digital Twin Framework for IoT," 2023. [Online]. Available: https://eclipse.dev/ditto/
6. F. T. Liu, K. M. Ting, and Z.-H. Zhou, "Isolation Forest," in *Proc. IEEE ICDM*, 2008, pp. 413–422.
7. B. Schölkopf et al., "Estimating the Support of a High-Dimensional Distribution," *Neural Computation*, vol. 13, no. 7, 2001.
8. J. Goh et al., "Anomaly Detection in Cyber Physical Systems Using Recurrent Neural Networks," in *Proc. IEEE HASE*, 2017.
9. M. Kravchik and A. Shabtai, "Detecting Cyber Attacks in Industrial Control Systems Using Convolutional Neural Networks," in *Proc. ACM CPS-SPC*, 2018.
10. A. B. Arrieta et al., "Explainable Artificial Intelligence (XAI): Concepts, Taxonomies, Opportunities and Challenges," *Information Fusion*, vol. 58, 2020.
11. S. M. Lundberg and S.-I. Lee, "A Unified Approach to Interpreting Model Predictions (SHAP)," in *Proc. NeurIPS*, 2017.
12. L. Antwarg et al., "Explaining Anomalies Detected by Autoencoders Using Shapley Additive Explanations," *Expert Systems with Applications*, vol. 186, 2021.
13. R.-H. Hwang et al., "An Explainable AI-Based Intrusion Detection System Using SHAP," *IEEE Access*, 2022.
14. W. Tounsi and H. Rais, "A Survey on Technical Threat Intelligence in the Age of Sophisticated Cyber Attacks," *Computers & Security*, vol. 72, 2018.
15. X. Liao et al., "Acing the IOC Game: Toward Automatic Discovery and Analysis of Open-Source Cyber Threat Intelligence," in *Proc. ACM CCS*, 2016.
16. N. Sun et al., "HinCTI: A Cyber Threat Intelligence Modeling and Identification System Based on Heterogeneous Information Network," *IEEE TKDE*, 2021.
17. X. Ou, S. Govindavajhala, and A. W. Appel, "MulVAL: A Logic-Based Network Security Analyzer," in *Proc. USENIX Security*, 2005.
18. S. Jajodia, S. Noel, and B. O'Berry, "Topological Analysis of Network Attack Vulnerability," in *Managing Cyber Threats*, Springer, 2005.
19. S. M. Milajerdi et al., "HOLMES: Real-Time APT Detection through Correlation of Suspicious Information Flows," in *Proc. IEEE S&P*, 2019.
20. A. Nadeem et al., "Alert-Driven Attack Graph Generation Using S-PDFA (SAGE)," *IEEE Trans. Dependable Secure Comput.*, 2021.
21. B. E. Strom et al., "MITRE ATT&CK: Design and Philosophy," MITRE Corp., Tech. Rep., 2018.
22. S. R. Pokhrel et al., "Cybersecurity of IoT-Enabled Smart Supply Chains: A Survey," *IEEE Internet of Things Journal*, 2023.
