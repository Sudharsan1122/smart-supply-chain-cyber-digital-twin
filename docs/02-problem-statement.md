# Problem Statement

## Real-World Evidence

Modern supply chains have suffered catastrophic cyber attacks in recent years:

| Incident | Year | Impact |
|----------|------|--------|
| **NotPetya** | 2017 | $10B global damage, Maersk lost $350M, 49,000 computers wiped |
| **SolarWinds** | 2020 | 18,000 organizations compromised, undetected for 9 months |
| **Colonial Pipeline** | 2021 | 5,500-mile shutdown, $5M ransom, fuel shortages |
| **MOVEit** | 2023 | 2,120 organizations, 62M individuals affected |
| **Nagoya Port** | 2023 | 3-day shutdown, 37 vessels stranded, 20,000 containers delayed |

## Why Current Tools Fail

Traditional cybersecurity tools (Firewalls, IDS/IPS, SIEM) fail in four
measurable ways:

### 1. Reactive Detection
Signatures only catch known attacks. IBM's Cost of a Data Breach Report
(2023) reports a **9-month mean time to detect** advanced supply chain
attacks.

### 2. No Topology Awareness
No existing tool models parent-child relationships between trucks →
gateways → warehouses → APIs → databases. Blast radius is computed
manually or not at all.

### 3. No Live Threat Intelligence in Risk Scoring
Risk scores are static. They do not reweight when IOCs are confirmed
malicious by external feeds (VirusTotal, AbuseIPDB, AlienVault OTX).

### 4. No Automated Triage
Analysts manually investigate every alert. Ponemon Institute reports
that **68% of SOC analysts experience alert fatigue**, leading to
delayed containment.

## Proposed Solution

A **Smart Supply Chain Cyber Digital Twin** that:
1. Mirrors 32 supply chain assets in real-time (NetworkX + Eclipse Ditto)
2. Detects anomalies with dual rule + ML engines
3. Enriches IOCs against live threat intelligence (C8 contribution)
4. Reconstructs attacks as MITRE ATT&CK-mapped stories
5. Computes topology-driven blast radius
6. Auto-triages every detection with measurable precision/recall/F1

Measured results: **Precision 0.89, Recall 1.00, F1 0.94** across 200+ tests.
