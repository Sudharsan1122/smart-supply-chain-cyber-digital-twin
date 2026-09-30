# Literature Review — Smart Supply Chain Cyber Digital Twin

## 1. Digital Twins for Cybersecurity and Critical Infrastructure
Digital Twins—originally pioneered in aerospace and smart manufacturing for predictive maintenance—have recently been adapted to cybersecurity monitoring. Eckhart and Ekelhart [1], [2] introduced specification-based security digital twins (`CPS-TWIN`) that mirror industrial control state from passive network traffic. Dietz et al. [3] proposed integrating security simulations into asset administration shells, while Bitton et al. [4] constructed a digital twin for water distribution testbeds. Industry-grade frameworks such as **Eclipse Ditto** [5] standardize the representation of IoT assets as JSON-based `Things` with static `attributes` and dynamic `features`. However, prior digital twin security frameworks focus almost exclusively on single-factory PLC replication rather than distributed, mobile supply chain fleets, and lack native graph-theoretic blast-radius propagation.

## 2. Anomaly Detection and Explainable AI (XAI) in Cyber-Physical Systems
Unsupervised machine learning models—including Isolation Forests [6], One-Class SVMs [7], and LSTM autoencoders [8], [9]—are widely deployed for detecting zero-day telemetry deviations in CPS. While deep autoencoders capture temporal correlations, they operate as opaque "black boxes" that fail to justify *why* an alert was raised, eroding SOC analyst trust [10]. Lundberg and Lee [11] introduced **SHAP (SHapley Additive exPlanations)**, unifying cooperative game theory with local feature attribution. Recent studies by Antwarg et al. [12] and Hwang et al. [13] demonstrated SHAP on tabular intrusion datasets (`NSL-KDD`, `CICIDS2017`), yet few systems integrate real-time KernelSHAP attributions directly into an operational Digital Twin triage console alongside deterministic domain rules and geospatial Haversine geofencing.

## 3. Threat Intelligence Enrichment and Dynamic Risk Scoring
Cyber Threat Intelligence (CTI) platforms aggregate Indicators of Compromise (IOCs) from community and commercial feeds such as VirusTotal, AbuseIPDB, and AlienVault OTX [14], [15]. Tounsi and Rais [14] surveyed technical CTI sharing standards (`STIX/TAXII`), while Sun et al. [16] proposed graph-based IOC correlation. Nevertheless, in existing enterprise pipelines, CTI enrichment is decoupled from quantitative cyber-physical risk scoring: IOC lookups are displayed as passive metadata in a SIEM ticket rather than mathematically reweighting the compromised asset's real-time risk score and cascading that elevated risk to dependent supply chain nodes (**Gap G6 / Contribution C8**).

## 4. Attack Reconstruction and Topological Blast Radius Modeling
MulVAL [17] and topological vulnerability analysis (TVA) [18] model multi-step network exploitation using static pre-condition/post-condition logic graphs. Later works by Milajerdi et al. (`HOLMES`) [19] and Nadeem et al. (`SAGE`) [20] reconstruct attack campaigns mapped to the **MITRE ATT&CK** framework [21] from host audit logs or alert streams. However, existing provenance and alert-correlation graphs do not combine real-time physical telemetry (GPS trajectories, cold-chain temperature, door tamper sensors) with enterprise IT alerts (Wazuh HIDS, Suricata NIDS) and interactive historical timeline playback [22].

## 5. Comparative Gap Matrix (22 Papers Across 8 Research Gaps)

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
