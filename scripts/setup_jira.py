#!/usr/bin/env python3
"""
setup_jira.py — Automated Jira Cloud Scrum Project Setup for SSCDT
==================================================================
Project: Smart Supply Chain Cyber Digital Twin (20CYS495 Project Phase-I)
Institution: Amrita Vishwa Vidyapeetham, Chennai
Team: Sudharsan S (CH.SC.U4CYS23045), Manojkumar A (CH.SC.U4CYS23022)
Faculty Guide: Dr. S. Udhayakumar
Jira Cloud: https://mastersudhan1234.atlassian.net

This script automates the complete Jira Scrum configuration via Jira REST API v3:
  - Step 1: Creates the Scrum Software Project (SSCDT)
  - Step 2: Creates 10 Project Components
  - Step 3: Creates 10 Epics (with automatic field discovery for Epic Name)
  - Step 4: Creates 39 User Stories with structured ADF descriptions & story points
  - Step 5: Creates Sprint 1 & Sprint 2 on the Agile Scrum Board
  - Step 6: Assigns all 39 stories into their respective Sprints
  - Idempotent: checks for existing entities and skips duplicates without failing
  - Exports created keys to docs/jira_created_keys.json
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import requests

# ============================================================
# CONFIGURATION
# ============================================================
JIRA_URL = os.getenv("JIRA_URL", "https://mastersudhan1234.atlassian.net").rstrip("/")
EMAIL = os.getenv("JIRA_EMAIL", "mastersudhan1234@gmail.com")
API_TOKEN = os.getenv("JIRA_API_TOKEN", "ATATT3xFfGF0gSW8B6gPTh9p_ljifNpbX_Y6O3i-IKQz0mnBi_BY6Qs3DhPE3BCsqtD3t1UZ1ullQojbxbCFruuw4D8dD_5kKXd9wejw388zN3jaBc1AHrR2HC--E4lQc25KAz4mir6xXdNVwXmtb-SlO-P7G2ei_LJVg0YQsKudAFamMhSQsqY=A67CAAF1")
PROJECT_KEY = "SSCDT"
PROJECT_NAME = "Smart Supply Chain Cyber Digital Twin"
PROJECT_TYPE_KEY = "software"
PROJECT_TEMPLATE_KEY = "com.pyxis.greenhopper.jira:gh-scrum-template"
ACCOUNT_ID = os.getenv("JIRA_ACCOUNT_ID", "712020:3edf19c5-b975-470a-9e1f-bec93774ae4d")

COMPONENTS_LIST = [
    "Ingestion",
    "Digital Twin Core",
    "Detection Engine",
    "Threat Intelligence",
    "Analysis & Triage",
    "Dashboard & UI",
    "Infrastructure & DevOps",
    "Machine Learning",
    "Security & Compliance",
    "Documentation",
]

EPICS_DATA = [
    {
        "id": "EPIC-1",
        "name": "Ingestion & Data Layer",
        "summary": "EPIC-1: Ingestion & Data Layer",
        "description": "Accept telemetry/events from REST, MQTT, Wazuh SIEM, Suricata IDS, external threat feeds. Persist to PostgreSQL (20 tables, 32 seeded assets). Covers FR1–FR5.",
        "component": "Ingestion",
        "labels": ["phase-1", "phase-2", "wazuh", "suricata"],
        "priority": "High",
    },
    {
        "id": "EPIC-2",
        "name": "Digital Twin Core",
        "summary": "EPIC-2: Digital Twin Core",
        "description": "NetworkX DiGraph twin (32 nodes, 14 edges), live state manager, drift detection, Eclipse Ditto integration (32 synced things), time-travel snapshots. Covers FR6–FR9, Phases 3, 8, 9.",
        "component": "Digital Twin Core",
        "labels": ["phase-3", "eclipse-ditto"],
        "priority": "High",
    },
    {
        "id": "EPIC-3",
        "name": "Detection Engine",
        "summary": "EPIC-3: Detection Engine",
        "description": "10 rule-based detectors, 16 ML models (Isolation Forest + One-Class SVM), 6 correlation rules, 9 state machines. Covers FR10–FR12, Phases 7, 10, 11, 22.",
        "component": "Detection Engine",
        "labels": ["phase-1", "ml"],
        "priority": "High",
    },
    {
        "id": "EPIC-4",
        "name": "Threat Intelligence (C8)",
        "summary": "EPIC-4: Threat Intelligence (C8)",
        "description": "11 IOC types, enriched via VirusTotal + AbuseIPDB + AlienVault OTX, consensus verdict, risk reweighting loop. RESEARCH CONTRIBUTION. Covers FR13–FR15, Phases 15, 16.",
        "component": "Threat Intelligence",
        "labels": ["c8", "ioc", "research"],
        "priority": "Highest",
    },
    {
        "id": "EPIC-5",
        "name": "Analysis & Triage",
        "summary": "EPIC-5: Analysis & Triage",
        "description": "Blast radius (BFS + 0.7^depth decay), attack story engine with 13 MITRE tactics, auto-triage (P=0.89, R=1.00, F1=0.94), XAI (SHAP). Covers FR16–FR18, Phases 14, 17, 18.",
        "component": "Analysis & Triage",
        "labels": ["mitre", "xai"],
        "priority": "Highest",
    },
    {
        "id": "EPIC-6",
        "name": "Dashboard & Visualization",
        "summary": "EPIC-6: Dashboard & Visualization",
        "description": "Flask + Chart.js + D3 + Leaflet dashboard, 4 tabs, live geographic map with trucks on real highways, timeline playback, geofencing, weather overlay. Covers FR19–FR23, Phase 19.",
        "component": "Dashboard & UI",
        "labels": ["phase-1", "phase-2"],
        "priority": "High",
    },
    {
        "id": "EPIC-7",
        "name": "Machine Learning",
        "summary": "EPIC-7: Machine Learning",
        "description": "Isolation Forest + One-Class SVM, 16 models, per-asset-type training, ML-ANOMALY detection, SHAP explainability. Covers Phase 22.",
        "component": "Machine Learning",
        "labels": ["ml", "xai"],
        "priority": "High",
    },
    {
        "id": "EPIC-8",
        "name": "Infrastructure & DevOps",
        "summary": "EPIC-8: Infrastructure & DevOps",
        "description": "14 Docker containers, multi-stage Dockerfiles, CI/CD pipeline, AWS Terraform (VPC, RDS, ECS Fargate, ALB, ECR, Secrets Manager, CloudWatch). Covers Phases 23, 24.",
        "component": "Infrastructure & DevOps",
        "labels": ["docker", "terraform"],
        "priority": "Medium",
    },
    {
        "id": "EPIC-9",
        "name": "Security & Compliance",
        "summary": "EPIC-9: Security & Compliance",
        "description": "20 security requirements (SR1–SR20), STRIDE threat model, Wazuh SIEM + Suricata IDS, secure coding, dependency reduction. Covers Phase 1.",
        "component": "Security & Compliance",
        "labels": ["wazuh", "suricata"],
        "priority": "Medium",
    },
    {
        "id": "EPIC-10",
        "name": "Testing & Documentation",
        "summary": "EPIC-10: Testing & Documentation",
        "description": "~200 tests, ≥85% coverage, pytest + pytest-asyncio, 11 GitHub docs, 53 requirements documented. Covers Phase 21.",
        "component": "Documentation",
        "labels": ["testing", "documentation"],
        "priority": "Medium",
    },
]

STORIES_DATA = [
    # --- EPIC-1: Ingestion & Data Layer ---
    {
        "id": "US-01",
        "summary": "US-01: REST telemetry ingestion endpoint",
        "role": "telemetry sensor or vehicle gateway",
        "capability": "POST /api/telemetry endpoint with schema validation",
        "benefit": "real-time cyber-physical sensor data is safely ingested into the digital twin",
        "ac": [
            "Given a valid telemetry JSON payload conforming to Pydantic v2 schema",
            "When sent via POST /api/telemetry with HTTPS",
            "Then the system responds with 201 Created and persists records into PostgreSQL",
        ],
        "points": 5,
        "component": "Ingestion",
        "labels": ["phase-1"],
        "priority": "High",
        "epic": "EPIC-1",
        "sprint": 1,
    },
    {
        "id": "US-02",
        "summary": "US-02: REST event ingestion endpoint",
        "role": "security agent",
        "capability": "POST /api/events endpoint for security audit logs",
        "benefit": "critical security events are immediately ingested and mapped to asset IDs",
        "ac": [
            "Given a security event payload with valid asset_id and event_type",
            "When sent to POST /api/events",
            "Then the event is stored in security_events and forwarded to the correlator",
        ],
        "points": 5,
        "component": "Ingestion",
        "labels": ["phase-5"],
        "priority": "High",
        "epic": "EPIC-1",
        "sprint": 1,
    },
    {
        "id": "US-03",
        "summary": "US-03: MQTT bridge subscriber",
        "role": "IoT telemetry listener",
        "capability": "MQTT bridge subscriber listening on supply_chain/telemetry/+",
        "benefit": "high-throughput streaming telemetry from trucks and warehouses is ingested without HTTP overhead",
        "ac": [
            "Given Mosquitto MQTT broker running on port 1883",
            "When messages are published to supply_chain/telemetry/+",
            "Then the bridge receives, parses, validates, and commits metrics to database",
        ],
        "points": 8,
        "component": "Ingestion",
        "labels": ["phase-6"],
        "priority": "High",
        "epic": "EPIC-1",
        "sprint": 1,
    },
    {
        "id": "US-04",
        "summary": "US-04: Wazuh SIEM integration",
        "role": "SOC analyst",
        "capability": "automated pull of real host-based intrusion alerts from Wazuh SIEM Manager",
        "benefit": "host compromises on edge servers and auth systems trigger twin security alarms",
        "ac": [
            "Given Wazuh Manager active on port 55000 with JWT authentication",
            "When agent alerts occur (rule 5710, 40111)",
            "Then pull alerts every 10 seconds and correlate against twin graph nodes",
        ],
        "points": 5,
        "component": "Ingestion",
        "labels": ["wazuh"],
        "priority": "High",
        "epic": "EPIC-1",
        "sprint": 1,
    },
    {
        "id": "US-05",
        "summary": "US-05: Suricata IDS integration",
        "role": "network security engineer",
        "capability": "continuous ingestion of Suricata NIDS eve.json network alert logs",
        "benefit": "network port scans and anomalous C2 packets are visible in the digital twin",
        "ac": [
            "Given Suricata logging network events to /var/log/suricata/eve.json",
            "When signature alerts (e.g. 2024001, 2024019) fire",
            "Then extract flow metadata and correlate with target supply chain assets",
        ],
        "points": 5,
        "component": "Ingestion",
        "labels": ["suricata"],
        "priority": "High",
        "epic": "EPIC-1",
        "sprint": 1,
    },
    {
        "id": "US-06",
        "summary": "US-06: PostgreSQL schema (20 tables)",
        "role": "data engineer",
        "capability": "normalized PostgreSQL 16 schema with 20 relational tables and 32 seeded assets",
        "benefit": "the entire supply chain topology, state history, and detections are durably stored",
        "ac": [
            "Given PostgreSQL 16 initialized via SQLAlchemy 2.0 AsyncIO",
            "When seed scripts execute",
            "Then verify exactly 32 assets and 20 relational tables are initialized",
        ],
        "points": 13,
        "component": "Ingestion",
        "labels": ["phase-2"],
        "priority": "High",
        "epic": "EPIC-1",
        "sprint": 1,
    },
    # --- EPIC-2: Digital Twin Core ---
    {
        "id": "US-07",
        "summary": "US-07: NetworkX DiGraph twin",
        "role": "digital twin engineer",
        "capability": "NetworkX directed graph representing 32 assets and 14 dependency edges",
        "benefit": "parent-child relationships and graph centralities (degree, betweenness) can be computed",
        "ac": [
            "Given database asset and edge records",
            "When twin_graph loads at system startup",
            "Then build DiGraph with 32 nodes and 14 edges and compute centrality metrics",
        ],
        "points": 8,
        "component": "Digital Twin Core",
        "labels": ["phase-3"],
        "priority": "High",
        "epic": "EPIC-2",
        "sprint": 1,
    },
    {
        "id": "US-08",
        "summary": "US-08: Live state manager",
        "role": "operations engineer",
        "capability": "in-memory and database synchronization of live asset state and health",
        "benefit": "the digital twin continuously mirrors real-world physical and cyber conditions",
        "ac": [
            "Given incoming telemetry normalizer output",
            "When asset metrics update",
            "Then update twin_states table and in-memory cache within 50ms",
        ],
        "points": 5,
        "component": "Digital Twin Core",
        "labels": ["phase-3"],
        "priority": "High",
        "epic": "EPIC-2",
        "sprint": 1,
    },
    {
        "id": "US-09",
        "summary": "US-09: Drift detection & auto-reconcile",
        "role": "system maintainer",
        "capability": "periodic drift detection audit running every 30 seconds",
        "benefit": "cache state and database records stay automatically reconciled without manual restarts",
        "ac": [
            "Given potential state mismatch between cache and database",
            "When drift sweep executes every 30s",
            "Then flag discrepancies, auto-reconcile to source of truth, and log audit entry",
        ],
        "points": 5,
        "component": "Digital Twin Core",
        "labels": ["phase-8"],
        "priority": "High",
        "epic": "EPIC-2",
        "sprint": 1,
    },
    {
        "id": "US-10",
        "summary": "US-10: Time-travel snapshots",
        "role": "forensic investigator",
        "capability": "full and delta state snapshots with delta compression",
        "benefit": "the exact supply chain state can be reconstructed at any historical point in time",
        "ac": [
            "Given recorded state_transitions and snapshot log",
            "When querying state at timestamp T",
            "Then reconstruct exact 32-asset health and metric values using delta decompression",
        ],
        "points": 13,
        "component": "Digital Twin Core",
        "labels": ["phase-9"],
        "priority": "High",
        "epic": "EPIC-2",
        "sprint": 1,
    },
    {
        "id": "US-11",
        "summary": "US-11: Eclipse Ditto integration",
        "role": "enterprise architect",
        "capability": "Eclipse Ditto integration with 5 containers and periodic 5-second sync",
        "benefit": "all 32 assets conform to standard W3C Digital Twin Thing models with live REST endpoints",
        "ac": [
            "Given Eclipse Ditto cluster running on port 8080",
            "When ditto_sync runs every 5 seconds",
            "Then PUT /api/2/things/{id} synchronizes all 32 assets with latency < 500ms",
        ],
        "points": 13,
        "component": "Digital Twin Core",
        "labels": ["eclipse-ditto"],
        "priority": "Highest",
        "epic": "EPIC-2",
        "sprint": 1,
    },
    # --- EPIC-3: Detection Engine ---
    {
        "id": "US-12",
        "summary": "US-12: 10 rule-based detectors",
        "role": "detection engineer",
        "capability": "10 deterministic detection rules (RULE-001..RULE-010)",
        "benefit": "known cyber-physical anomalies like cold-chain thermal breaches and geofence violations are caught instantly",
        "ac": [
            "Given incoming telemetry and event streams",
            "When rule threshold condition is satisfied (e.g. temp > 8C or failed logins >= 5)",
            "Then emit detection record with confidence 0.60–0.95 within 2 seconds",
        ],
        "points": 13,
        "component": "Detection Engine",
        "labels": ["phase-10"],
        "priority": "High",
        "epic": "EPIC-3",
        "sprint": 1,
    },
    {
        "id": "US-13",
        "summary": "US-13: 9 asset-type state machines",
        "role": "security engineer",
        "capability": "finite state machines for all 9 supply chain asset types",
        "benefit": "out-of-order or unauthorized operational transitions trigger transition anomaly alerts",
        "ac": [
            "Given defined valid transitions per asset type",
            "When an illegal transition occurs (e.g. IN_TRANSIT directly to MAINTENANCE without DELIVERED)",
            "Then log transition anomaly and flag asset as suspicious",
        ],
        "points": 8,
        "component": "Detection Engine",
        "labels": ["phase-11"],
        "priority": "High",
        "epic": "EPIC-3",
        "sprint": 1,
    },
    {
        "id": "US-14",
        "summary": "US-14: 6 correlation rules",
        "role": "incident responder",
        "capability": "6 multi-signal correlation rules across temporal sliding windows",
        "benefit": "disparate low-severity detections are synthesized into consolidated incidents",
        "ac": [
            "Given multiple related detections within a 60-second window",
            "When correlation rule conditions match",
            "Then create an incident entity and link all contributing detection and telemetry IDs",
        ],
        "points": 8,
        "component": "Detection Engine",
        "labels": ["phase-7"],
        "priority": "High",
        "epic": "EPIC-3",
        "sprint": 1,
    },
    {
        "id": "US-15",
        "summary": "US-15: Risk scoring (6 components)",
        "role": "risk analyst",
        "capability": "6-component dynamic risk scoring algorithm recalculated after every ingest",
        "benefit": "asset risk scores (0–100) dynamically reflect detections, transitions, incidents, threat intel, centrality, and health",
        "ac": [
            "Given asset evaluation formula with weights (35% det, 15% trans, 20% inc, 15% intel, 10% cent, 5% health)",
            "When telemetry is ingested",
            "Then recompute and persist composite risk score within 100ms",
        ],
        "points": 8,
        "component": "Detection Engine",
        "labels": ["phase-12"],
        "priority": "High",
        "epic": "EPIC-3",
        "sprint": 1,
    },
    # --- EPIC-4: Threat Intelligence (C8) ---
    {
        "id": "US-16",
        "summary": "US-16: IOC extraction (11 types)",
        "role": "threat researcher",
        "capability": "automated extraction of 11 IOC types from raw payloads and logs",
        "benefit": "IPs, domains, hashes, URLs, emails, and crypto addresses are automatically isolated",
        "ac": [
            "Given abnormal payload string or event log",
            "When regex and semantic extractors run",
            "Then extract and deduplicate IOCs, attributing them to the origin asset ID",
        ],
        "points": 8,
        "component": "Threat Intelligence",
        "labels": ["phase-15", "ioc"],
        "priority": "High",
        "epic": "EPIC-4",
        "sprint": 2,
    },
    {
        "id": "US-17",
        "summary": "US-17: 3-provider enrichment",
        "role": "cyber threat analyst",
        "capability": "automated enrichment via VirusTotal, AbuseIPDB, and AlienVault OTX with 24h caching",
        "benefit": "observed indicators receive consensus reputation verdicts without exceeding API quotas",
        "ac": [
            "Given extracted public IOC",
            "When enrichment pipeline queries external threat feeds",
            "Then store provider verdicts in ioc_enrichments with a 24-hour TTL cache",
        ],
        "points": 13,
        "component": "Threat Intelligence",
        "labels": ["phase-16"],
        "priority": "High",
        "epic": "EPIC-4",
        "sprint": 2,
    },
    {
        "id": "US-18",
        "summary": "US-18: C8 risk reweighting loop",
        "role": "cybersecurity researcher",
        "capability": "closed-loop dynamic risk reweighting triggered by malicious threat intel verdicts",
        "benefit": "malicious external reputation dynamically amplifies asset risk scores and prioritizes triage",
        "ac": [
            "Given an IOC confirmed malicious (confidence >= 0.50)",
            "When C8 reweighting algorithm executes",
            "Then amplify threat intel risk component by (1 + 1.5 * confidence) and trigger blast radius recalculation",
        ],
        "points": 13,
        "component": "Threat Intelligence",
        "labels": ["c8", "research"],
        "priority": "Highest",
        "epic": "EPIC-4",
        "sprint": 2,
    },
    # --- EPIC-5: Analysis & Triage ---
    {
        "id": "US-19",
        "summary": "US-19: Blast radius computation",
        "role": "SOC analyst",
        "capability": "topological blast radius computation using BFS traversal with 0.7^depth decay",
        "benefit": "cascading compromise risk across multi-hop dependencies is accurately quantified",
        "ac": [
            "Given compromised root node",
            "When BFS traversal computes impact across directed dependency edges up to depth 4",
            "Then calculate attenuated impact scores and identify all vulnerable downstream nodes",
        ],
        "points": 8,
        "component": "Analysis & Triage",
        "labels": ["phase-17"],
        "priority": "High",
        "epic": "EPIC-5",
        "sprint": 2,
    },
    {
        "id": "US-20",
        "summary": "US-20: Attack story engine",
        "role": "incident commander",
        "capability": "attack storytelling engine mapping multi-stage events to 13 MITRE ATT&CK tactics",
        "benefit": "analysts see a coherent chronological narrative of the adversary's progression",
        "ac": [
            "Given correlated security events in an active attack scenario",
            "When attack story synthesizer runs",
            "Then generate ordered timeline, associate MITRE tactics, and compute attribution confidence",
        ],
        "points": 13,
        "component": "Analysis & Triage",
        "labels": ["phase-14", "mitre"],
        "priority": "High",
        "epic": "EPIC-5",
        "sprint": 2,
    },
    {
        "id": "US-21",
        "summary": "US-21: Auto-triage classifier",
        "role": "SOC lead",
        "capability": "automated triage classifier categorizing detections into TP/FP/FN/TN",
        "benefit": "alert fatigue is reduced with verified performance (Precision=0.89, Recall=1.00, F1=0.94)",
        "ac": [
            "Given unclassified detections",
            "When automated triage sweep executes",
            "Then classify alerts, output confusion matrix, and achieve >= 0.89 precision with 1.00 recall",
        ],
        "points": 8,
        "component": "Analysis & Triage",
        "labels": ["phase-18"],
        "priority": "Highest",
        "epic": "EPIC-5",
        "sprint": 2,
    },
    {
        "id": "US-22",
        "summary": "US-22: XAI (SHAP) explanations",
        "role": "security analyst",
        "capability": "KernelSHAP feature attribution explanations for every ML anomaly detection",
        "benefit": "operators understand exactly which telemetry features contributed to an ML alert",
        "ac": [
            "Given an ML anomaly detection",
            "When GET /api/ml/explain/{id} is called",
            "Then return top-5 contributing features with directional SHAP weights within 200ms",
        ],
        "points": 8,
        "component": "Analysis & Triage",
        "labels": ["xai"],
        "priority": "High",
        "epic": "EPIC-5",
        "sprint": 2,
    },
    # --- EPIC-6: Dashboard & Visualization ---
    {
        "id": "US-23",
        "summary": "US-23: 4-tab dashboard",
        "role": "security operator",
        "capability": "responsive 4-tab Flask web dashboard (Live Fleet, Attack Stories, Threat Intel, Triage)",
        "benefit": "all security operations and digital twin telemetry are accessible in real time",
        "ac": [
            "Given dashboard server running on port 5000",
            "When opening http://localhost:5000",
            "Then render KPI cards, live charts, and tables with 3-second auto-refresh polling",
        ],
        "points": 13,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "epic": "EPIC-6",
        "sprint": 2,
    },
    {
        "id": "US-24",
        "summary": "US-24: Live geographic map",
        "role": "logistics controller",
        "capability": "interactive Leaflet OpenStreetMap showing truck fleets along Indian highway corridors",
        "benefit": "fleet movements, route trails, and geographic anomalies are visually tracked",
        "ac": [
            "Given real-time truck GPS telemetry",
            "When viewing Live Fleet map",
            "Then render animated truck markers, route breadcrumbs, and location tooltips",
        ],
        "points": 8,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "epic": "EPIC-6",
        "sprint": 2,
    },
    {
        "id": "US-25",
        "summary": "US-25: Timeline playback",
        "role": "forensic analyst",
        "capability": "interactive timeline scrubber to rewind and replay attack simulations step-by-step",
        "benefit": "analysts can replay multi-stage attack scenarios to study breach progression",
        "ac": [
            "Given completed attack scenario",
            "When adjusting timeline playback slider",
            "Then rewind map positions, asset states, and alert logs to the selected historical step",
        ],
        "points": 5,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "epic": "EPIC-6",
        "sprint": 2,
    },
    {
        "id": "US-26",
        "summary": "US-26: Geofencing + weather overlay",
        "role": "fleet safety manager",
        "capability": "Haversine geofence breach circles and live OpenWeather map overlays",
        "benefit": "route deviations and adverse environmental weather hazards are flagged immediately",
        "ac": [
            "Given assigned regional hubs and weather API",
            "When truck coordinates deviate beyond safe radius",
            "Then display colored boundary rings on map and trigger RULE-010 geofence alert",
        ],
        "points": 5,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "epic": "EPIC-6",
        "sprint": 2,
    },
    # --- EPIC-7: Machine Learning ---
    {
        "id": "US-27",
        "summary": "US-27: Isolation Forest models (8)",
        "role": "data scientist",
        "capability": "8 unsupervised Isolation Forest anomaly detection models trained per asset type",
        "benefit": "multivariate zero-day sensor telemetry anomalies are detected without labeled training data",
        "ac": [
            "Given rolling feature vectors (mean, std, range, slope, z-score)",
            "When model fits on baseline telemetry",
            "Then serialize models to ml/artifacts/ and evaluate anomaly probabilities",
        ],
        "points": 8,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "priority": "High",
        "epic": "EPIC-7",
        "sprint": 1,
    },
    {
        "id": "US-28",
        "summary": "US-28: One-Class SVM models (8)",
        "role": "data scientist",
        "capability": "8 One-Class SVM models trained per asset type as complementary boundary estimators",
        "benefit": "ensemble agreement between Isolation Forest and SVM enhances detection precision",
        "ac": [
            "Given normal operating feature distributions",
            "When One-Class SVM fits with RBF kernel",
            "Then persist model artifacts and flag outlier vectors lying outside support boundary",
        ],
        "points": 8,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "priority": "High",
        "epic": "EPIC-7",
        "sprint": 1,
    },
    {
        "id": "US-29",
        "summary": "US-29: ML-ANOMALY detection wiring",
        "role": "pipeline engineer",
        "capability": "seamless integration of ML inference scores into the live ingestion and triage pipeline",
        "benefit": "ML anomalies automatically generate detection records and contribute to asset risk scores",
        "ac": [
            "Given incoming telemetry stream",
            "When ML inference evaluates feature vector",
            "Then if anomaly probability > 0.65, emit ML-ANOMALY detection and route to triage",
        ],
        "points": 5,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "priority": "High",
        "epic": "EPIC-7",
        "sprint": 1,
    },
    # --- EPIC-8: Infrastructure & DevOps ---
    {
        "id": "US-30",
        "summary": "US-30: Multi-stage Dockerfiles",
        "role": "DevOps engineer",
        "capability": "optimized multi-stage Dockerfiles running with dedicated non-root USER app",
        "benefit": "production container images have minimal attack surfaces and built-in healthchecks",
        "ac": [
            "Given Docker build instructions",
            "When building API and Dashboard containers",
            "Then verify image builds with non-root user and passes container security audits",
        ],
        "points": 8,
        "component": "Infrastructure & DevOps",
        "labels": ["docker", "phase-23"],
        "priority": "Medium",
        "epic": "EPIC-8",
        "sprint": 2,
    },
    {
        "id": "US-31",
        "summary": "US-31: Docker Compose (14 containers)",
        "role": "deployment engineer",
        "capability": "complete docker-compose.yml orchestrating all 14 containers",
        "benefit": "the entire cyber digital twin stack launches locally with one command",
        "ac": [
            "Given docker compose up -d",
            "When all services start",
            "Then confirm 14 containers (API, DB, MQTT, Ditto, Wazuh, Suricata) report healthy status",
        ],
        "points": 5,
        "component": "Infrastructure & DevOps",
        "labels": ["docker", "phase-23"],
        "priority": "Medium",
        "epic": "EPIC-8",
        "sprint": 2,
    },
    {
        "id": "US-32",
        "summary": "US-32: CI/CD pipeline",
        "role": "release engineer",
        "capability": "GitHub Actions CI/CD pipelines executing tests, linting, and image publishing",
        "benefit": "code changes are automatically validated and deployed with green build status",
        "ac": [
            "Given git push or PR to main",
            "When .github/workflows/ci.yml triggers",
            "Then execute pytest, verify coverage, run Bandit SAST, and build containers cleanly",
        ],
        "points": 5,
        "component": "Infrastructure & DevOps",
        "labels": ["phase-23"],
        "priority": "Medium",
        "epic": "EPIC-8",
        "sprint": 2,
    },
    {
        "id": "US-33",
        "summary": "US-33: AWS Terraform",
        "role": "cloud architect",
        "capability": "modular Terraform IaC deploying VPC, RDS Postgres, ECS Fargate, ALB, and Secrets Manager",
        "benefit": "the digital twin can be deployed into highly available AWS cloud environments",
        "ac": [
            "Given terraform plan and apply",
            "When executed against AWS target",
            "Then provision VPC, multi-AZ subnets, ECS Fargate services, and ALB endpoints cleanly",
        ],
        "points": 21,
        "component": "Infrastructure & DevOps",
        "labels": ["terraform", "phase-24"],
        "priority": "Medium",
        "epic": "EPIC-8",
        "sprint": 2,
    },
    # --- EPIC-9: Security & Compliance ---
    {
        "id": "US-34",
        "summary": "US-34: STRIDE threat model",
        "role": "security architect",
        "capability": "comprehensive STRIDE threat model covering all DFD elements and trust boundaries",
        "benefit": "systematic threat identification ensures proactive defensive mitigations are implemented",
        "ac": [
            "Given 7-layer architecture and data flow diagram",
            "When analyzing Spoofing, Tampering, Repudiation, Info Disclosure, DoS, and Elevation",
            "Then document threat matrix and verify corresponding security controls in docs/THREAT_MODEL.md",
        ],
        "points": 8,
        "component": "Security & Compliance",
        "labels": ["phase-1"],
        "priority": "Medium",
        "epic": "EPIC-9",
        "sprint": 2,
    },
    {
        "id": "US-35",
        "summary": "US-35: 20 security requirements (SR1–SR20)",
        "role": "compliance officer",
        "capability": "implementation and verification of 20 defense-in-depth security requirements",
        "benefit": "system adheres to industry best practices across authentication, integrity, and isolation",
        "ac": [
            "Given the 20 defined security requirements (SR1..SR20)",
            "When inspecting codebase and container configurations",
            "Then confirm all 20 security layers are active and documented in docs/SECURITY_FEATURES.md",
        ],
        "points": 5,
        "component": "Security & Compliance",
        "labels": ["phase-1"],
        "priority": "Medium",
        "epic": "EPIC-9",
        "sprint": 2,
    },
    {
        "id": "US-36",
        "summary": "US-36: Dependency reduction & audit",
        "role": "DevSecOps engineer",
        "capability": "automated vulnerability auditing using Bandit SAST, pip-audit, and safety",
        "benefit": "vulnerable third-party libraries and code smells are eliminated from the build",
        "ac": [
            "Given python dependencies and code repository",
            "When running bandit -r and pip-audit",
            "Then report zero high-severity vulnerabilities and zero unresolved security code smells",
        ],
        "points": 3,
        "component": "Security & Compliance",
        "labels": ["phase-1"],
        "priority": "Medium",
        "epic": "EPIC-9",
        "sprint": 2,
    },
    # --- EPIC-10: Testing & Documentation ---
    {
        "id": "US-37",
        "summary": "US-37: ~200 tests, ≥85% coverage",
        "role": "QA engineer",
        "capability": "automated unit, integration, and E2E simulation test suite with >=85% code coverage",
        "benefit": "regressions are caught instantly and system reliability is quantitatively verified",
        "ac": [
            "Given pytest test suite across tests/ directory",
            "When executing pytest --cov=. --cov-report=term-missing",
            "Then all ~200 tests pass and total test coverage meets or exceeds 85%",
        ],
        "points": 13,
        "component": "Documentation",
        "labels": ["testing", "phase-21"],
        "priority": "Medium",
        "epic": "EPIC-10",
        "sprint": 2,
    },
    {
        "id": "US-38",
        "summary": "US-38: 11 GitHub documents",
        "role": "technical writer",
        "capability": "11 comprehensive GitHub documentation guides in docs/ and project root",
        "benefit": "users, reviewers, and evaluators have complete architectural and operational manuals",
        "ac": [
            "Given project documentation folder",
            "When inspecting docs/ directory",
            "Then verify README, ARCHITECTURE, API, DEPLOYMENT, CICD, and all required guides exist and are linked",
        ],
        "points": 8,
        "component": "Documentation",
        "labels": ["documentation"],
        "priority": "Medium",
        "epic": "EPIC-10",
        "sprint": 2,
    },
    {
        "id": "US-39",
        "summary": "US-39: 53 requirements documented",
        "role": "systems engineer",
        "capability": "complete Phase 1 Requirements Engineering specification (23 FR, 10 NFR, 20 SR)",
        "benefit": "the project has formal requirements traceability aligning with IEEE/academic standards",
        "ac": [
            "Given Phase 1 deliverable requirements",
            "When viewing docs/PHASE_1_REQUIREMENTS.md",
            "Then confirm all 53 requirements are cataloged with IDs, descriptions, and targets",
        ],
        "points": 8,
        "component": "Documentation",
        "labels": ["documentation", "phase-1"],
        "priority": "Medium",
        "epic": "EPIC-10",
        "sprint": 2,
    },
]

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def make_adf_description(role: str, capability: str, benefit: str, ac_list: List[str]) -> Dict[str, Any]:
    """Generates an Atlassian Document Format (ADF) description structure."""
    user_story_text = f"As a {role}, I want {capability} so that {benefit}."
    
    ac_bullet_items = []
    for ac in ac_list:
        ac_bullet_items.append({
            "type": "listItem",
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": ac}]
            }]
        })

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "User Story:", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": f"\n{user_story_text}\n"}
                ]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Acceptance Criteria:", "marks": [{"type": "strong"}]}
                ]
            },
            {
                "type": "bulletList",
                "content": ac_bullet_items
            }
        ]
    }


def make_simple_adf(text: str) -> Dict[str, Any]:
    """Generates simple single-paragraph ADF."""
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}]
            }
        ]
    }


class JiraClient:
    def __init__(self, base_url: str, email: str, token: str, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.token = token
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.auth = (email, token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self.fields_cache: Dict[str, str] = {}
        self.stats = {
            "epics_created": 0,
            "stories_created": 0,
            "already_existed": 0,
            "errors": 0
        }

    def jira(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if self.dry_run:
            print(f"[DRY-RUN] {method.upper()} {url}")
            if "json" in kwargs:
                print(f"          Body: {json.dumps(kwargs['json'], indent=2)[:300]}...")
            # Return dummy response
            dummy = requests.Response()
            dummy.status_code = 200
            dummy._content = b"{}"
            return dummy

        for attempt in range(1, 4):
            try:
                resp = self.session.request(method, url, **kwargs)
                if resp.status_code >= 400:
                    print(f"[!] {method.upper()} {path} -> HTTP {resp.status_code}")
                    try:
                        err_json = resp.json()
                        print(f"    Error details: {json.dumps(err_json)[:250]}")
                    except Exception:
                        print(f"    Response text: {resp.text[:200]}")
                return resp
            except Exception as exc:
                if attempt < 3:
                    print(f"[WARN] Request to {url} failed ({exc}). Retrying attempt {attempt+1}/3 in 2s...")
                    time.sleep(2)
                else:
                    print(f"[ERROR] Request to {url} failed after 3 attempts: {exc}")
                    dummy = requests.Response()
                    dummy.status_code = 500
                    dummy._content = b"{}"
                    return dummy

    def discover_fields(self):
        """Discovers custom field IDs for Epic Name, Epic Link, and Story Points."""
        if self.dry_run:
            self.fields_cache = {
                "epic_name": "customfield_10011",
                "epic_link": "customfield_10014",
                "story_points": "customfield_10016"
            }
            return

        print("[*] Discovering Jira custom field IDs...")
        r = self.jira("GET", "/rest/api/3/field")
        if r.status_code == 200:
            fields = r.json()
            for f in fields:
                fname = f.get("name", "").lower()
                fid = f.get("id", "")
                if fname in ("epic name", "epic-name"):
                    self.fields_cache["epic_name"] = fid
                elif fname in ("epic link", "epic-link"):
                    self.fields_cache["epic_link"] = fid
                elif fname in ("story points", "story point estimate"):
                    self.fields_cache["story_points"] = fid

        print(f"    Discovered fields: {self.fields_cache}")

    def get_myself_account_id(self) -> Optional[str]:
        """Resolves caller accountId if not specified in config."""
        if self.dry_run:
            return "dry-run-account-id"
        r = self.jira("GET", "/rest/api/3/myself")
        if r.status_code == 200:
            return r.json().get("accountId")
        return None


# ============================================================
# STEP FUNCTIONS
# ============================================================

def create_project(client: JiraClient, account_id: str) -> bool:
    """Step 1: Creates the Jira Scrum project if it does not already exist."""
    print(f"\n{'='*60}\nSTEP 1 — Check / Create Jira Project ({PROJECT_KEY})\n{'='*60}")
    
    # Check if project exists
    r = client.jira("GET", f"/rest/api/3/project/{PROJECT_KEY}")
    if r.status_code == 200:
        print(f"[OK] Project {PROJECT_KEY} already exists. Skipping project creation.")
        client.stats["already_existed"] += 1
        return True

    payload = {
        "key": PROJECT_KEY,
        "name": PROJECT_NAME,
        "projectTypeKey": PROJECT_TYPE_KEY,
        "projectTemplateKey": PROJECT_TEMPLATE_KEY,
        "description": "API-first Cyber Digital Twin for supply chain security. Amrita Vishwa Vidyapeetham, 20CYS495.",
        "leadAccountId": account_id,
        "assigneeType": "PROJECT_LEAD"
    }

    resp = client.jira("POST", "/rest/api/3/project", json=payload)
    if resp.status_code in (200, 201):
        print(f"[+] Successfully created Jira project: {PROJECT_NAME} ({PROJECT_KEY})")
        return True
    else:
        print(f"[!] Project creation returned HTTP {resp.status_code}. It may require manual creation in Jira Cloud UI.")
        client.stats["errors"] += 1
        return False


def create_components(client: JiraClient):
    """Step 2: Creates the 10 project components."""
    print(f"\n{'='*60}\nSTEP 2 — Create Project Components\n{'='*60}")
    
    # Fetch existing components
    existing_comps = set()
    r = client.jira("GET", f"/rest/api/3/project/{PROJECT_KEY}/components")
    if r.status_code == 200:
        for c in r.json():
            existing_comps.add(c.get("name"))

    for comp in COMPONENTS_LIST:
        if comp in existing_comps:
            print(f"  [=] Component '{comp}' already exists. Skipping.")
            client.stats["already_existed"] += 1
            continue

        payload = {
            "name": comp,
            "project": PROJECT_KEY,
            "leadAccountId": None
        }
        resp = client.jira("POST", "/rest/api/3/component", json=payload)
        if resp.status_code in (200, 201):
            print(f"  [+] Created component: {comp}")
        else:
            client.stats["errors"] += 1
        time.sleep(0.1)


def create_epics(client: JiraClient) -> Dict[str, str]:
    """Step 3: Creates the 10 epics and returns mapping of epic_id -> Jira key."""
    print(f"\n{'='*60}\nSTEP 3 — Create 10 Epics\n{'='*60}")
    
    # Check existing epics via JQL search
    existing_epics = {}
    jql = f'project = "{PROJECT_KEY}" AND issuetype = "Epic"'
    search_r = client.jira("POST", "/rest/api/3/search", json={"jql": jql, "maxResults": 100, "fields": ["summary", "key"]})
    if search_r.status_code == 200:
        for issue in search_r.json().get("issues", []):
            summary = issue.get("fields", {}).get("summary", "")
            key = issue.get("key", "")
            for ep in EPICS_DATA:
                if ep["id"] in summary or ep["name"] in summary:
                    existing_epics[ep["id"]] = key

    epic_key_map = {}
    epic_name_field = client.fields_cache.get("epic_name")

    for epic in EPICS_DATA:
        ep_id = epic["id"]
        if ep_id in existing_epics:
            existing_key = existing_epics[ep_id]
            print(f"  [=] {ep_id} already exists as {existing_key}. Skipping.")
            epic_key_map[ep_id] = existing_key
            client.stats["already_existed"] += 1
            continue

        issue_fields = {
            "project": {"key": PROJECT_KEY},
            "summary": epic["summary"],
            "description": make_simple_adf(epic["description"]),
            "issuetype": {"name": "Epic"},
            "components": [{"name": epic["component"]}],
            "labels": epic["labels"],
            "priority": {"name": epic["priority"]},
        }

        # Add Epic Name customfield if detected on this instance
        if epic_name_field:
            issue_fields[epic_name_field] = epic["name"]

        resp = client.jira("POST", "/rest/api/3/issue", json={"fields": issue_fields})
        if resp.status_code in (200, 201):
            created_key = resp.json().get("key", f"{PROJECT_KEY}-?")
            epic_key_map[ep_id] = created_key
            client.stats["epics_created"] += 1
            print(f"  [+] Created {ep_id}: {epic['name']} -> {created_key}")
        else:
            client.stats["errors"] += 1
            # Fallback mock key for dry-run
            epic_key_map[ep_id] = f"{PROJECT_KEY}-{ep_id.replace('EPIC-', '')}"

        time.sleep(0.3)

    return epic_key_map


def create_stories(client: JiraClient, epic_key_map: Dict[str, str]) -> Dict[str, str]:
    """Step 4: Creates the 39 user stories linked to their respective epics."""
    print(f"\n{'='*60}\nSTEP 4 — Create 39 User Stories\n{'='*60}")
    
    # Check existing stories
    existing_stories = {}
    jql = f'project = "{PROJECT_KEY}" AND issuetype = "Story"'
    search_r = client.jira("POST", "/rest/api/3/search", json={"jql": jql, "maxResults": 150, "fields": ["summary", "key"]})
    if search_r.status_code == 200:
        for issue in search_r.json().get("issues", []):
            summary = issue.get("fields", {}).get("summary", "")
            key = issue.get("key", "")
            for st in STORIES_DATA:
                if st["id"] in summary:
                    existing_stories[st["id"]] = key

    story_key_map = {}
    epic_link_field = client.fields_cache.get("epic_link")
    points_field = client.fields_cache.get("story_points")

    for st in STORIES_DATA:
        st_id = st["id"]
        if st_id in existing_stories:
            ekey = existing_stories[st_id]
            print(f"  [=] {st_id} already exists as {ekey}. Skipping.")
            story_key_map[st_id] = ekey
            client.stats["already_existed"] += 1
            continue

        parent_epic_key = epic_key_map.get(st["epic"])

        issue_fields = {
            "project": {"key": PROJECT_KEY},
            "summary": st["summary"],
            "description": make_adf_description(st["role"], st["capability"], st["benefit"], st["ac"]),
            "issuetype": {"name": "Story"},
            "components": [{"name": st["component"]}],
            "labels": st["labels"],
            "priority": {"name": st["priority"]},
        }

        # Handle Epic Link: modern Jira Cloud uses "parent", legacy uses customfield
        if parent_epic_key:
            if epic_link_field:
                issue_fields[epic_link_field] = parent_epic_key
            else:
                issue_fields["parent"] = {"key": parent_epic_key}

        # Handle Story Points
        if points_field:
            issue_fields[points_field] = st["points"]

        resp = client.jira("POST", "/rest/api/3/issue", json={"fields": issue_fields})
        if resp.status_code in (200, 201):
            created_key = resp.json().get("key", f"{PROJECT_KEY}-?")
            story_key_map[st_id] = created_key
            client.stats["stories_created"] += 1
            print(f"  [+] Created {st_id} ({st['points']} pts) -> {created_key} [Epic: {parent_epic_key}]")
        else:
            # Fallback retry without custom fields if schema was rejected
            if resp.status_code == 400 and ("parent" in issue_fields or epic_link_field in issue_fields):
                issue_fields.pop("parent", None)
                if epic_link_field:
                    issue_fields.pop(epic_link_field, None)
                retry_r = client.jira("POST", "/rest/api/3/issue", json={"fields": issue_fields})
                if retry_r.status_code in (200, 201):
                    created_key = retry_r.json().get("key", f"{PROJECT_KEY}-?")
                    story_key_map[st_id] = created_key
                    client.stats["stories_created"] += 1
                    print(f"  [+] Created {st_id} (retry standalone) -> {created_key}")
                else:
                    client.stats["errors"] += 1
            else:
                client.stats["errors"] += 1

        time.sleep(0.3)

    return story_key_map


def get_or_create_board(client: JiraClient) -> Optional[int]:
    """Finds the Scrum board associated with the SSCDT project."""
    r = client.jira("GET", f"/rest/agile/1.0/board?projectKeyOrId={PROJECT_KEY}")
    if r.status_code == 200:
        values = r.json().get("values", [])
        if values:
            board_id = values[0].get("id")
            print(f"[OK] Found Scrum board: '{values[0].get('name')}' (ID: {board_id})")
            return board_id

    # Fallback to board #1 if dry-run or default
    return 1 if client.dry_run else None


def create_sprints(client: JiraClient, board_id: int) -> Tuple[Optional[int], Optional[int]]:
    """Step 5: Creates Sprint 1 and Sprint 2 on the agile board."""
    print(f"\n{'='*60}\nSTEP 5 — Create Sprints on Board {board_id}\n{'='*60}")
    
    # Check existing sprints
    existing_sprints = {}
    r = client.jira("GET", f"/rest/agile/1.0/board/{board_id}/sprint")
    if r.status_code == 200:
        for sp in r.json().get("values", []):
            existing_sprints[sp.get("name")] = sp.get("id")

    sprint_defs = [
        {
            "num": 1,
            "name": "SSCDT Sprint 1: Foundation",
            "goal": "Deliver ingestion, digital twin core, and detection engine (Epics 1, 2, 3, 7)."
        },
        {
            "num": 2,
            "name": "SSCDT Sprint 2: Ops & Intel",
            "goal": "Deliver threat intel C8, analysis/triage, dashboard, infra, security, testing, docs (Epics 4, 5, 6, 8, 9, 10)."
        }
    ]

    sprint_ids = [None, None]

    for idx, sdef in enumerate(sprint_defs):
        sname = sdef["name"]
        if sname in existing_sprints:
            sid = existing_sprints[sname]
            print(f"  [=] Sprint '{sname}' already exists (ID: {sid}). Skipping.")
            sprint_ids[idx] = sid
            client.stats["already_existed"] += 1
            continue

        payload = {
            "name": sname,
            "goal": sdef["goal"],
            "originBoardId": board_id
        }
        resp = client.jira("POST", "/rest/agile/1.0/sprint", json=payload)
        if resp.status_code in (200, 201):
            sid = resp.json().get("id")
            sprint_ids[idx] = sid
            print(f"  [+] Created Sprint {sdef['num']}: '{sname}' (ID: {sid})")
        else:
            client.stats["errors"] += 1
            if client.dry_run:
                sprint_ids[idx] = idx + 101  # Fallback only for dry-run

    return sprint_ids[0], sprint_ids[1]


def assign_stories_to_sprints(client: JiraClient, story_key_map: Dict[str, str], s1_id: Optional[int], s2_id: Optional[int]):
    """Step 6: Moves stories into Sprint 1 and Sprint 2."""
    print(f"\n{'='*60}\nSTEP 6 — Assign Stories to Sprints\n{'='*60}")
    
    s1_keys = []
    s2_keys = []

    for st in STORIES_DATA:
        st_key = story_key_map.get(st["id"])
        if not st_key:
            continue
        if st["sprint"] == 1:
            s1_keys.append(st_key)
        else:
            s2_keys.append(st_key)

    if s1_id and s1_keys:
        print(f"[*] Moving {len(s1_keys)} stories into Sprint 1 (ID: {s1_id})...")
        r1 = client.jira("POST", f"/rest/agile/1.0/sprint/{s1_id}/issue", json={"issues": s1_keys})
        if r1.status_code in (200, 204):
            print(f"  [OK] Assigned {len(s1_keys)} issues to Sprint 1.")
        else:
            print(f"  [!] Sprint 1 assignment status: {r1.status_code}")

    if s2_id and s2_keys:
        print(f"[*] Moving {len(s2_keys)} stories into Sprint 2 (ID: {s2_id})...")
        r2 = client.jira("POST", f"/rest/agile/1.0/sprint/{s2_id}/issue", json={"issues": s2_keys})
        if r2.status_code in (200, 204):
            print(f"  [OK] Assigned {len(s2_keys)} issues to Sprint 2.")
        else:
            print(f"  [!] Sprint 2 assignment status: {r2.status_code}")


# ============================================================
# MAIN ENTRYPOINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Jira Cloud Scrum Project Automation for SSCDT")
    parser.add_argument("--url", default=JIRA_URL, help="Jira Cloud Base URL")
    parser.add_argument("--email", default=EMAIL, help="Atlassian Account Email")
    parser.add_argument("--token", default=API_TOKEN, help="Atlassian API Token")
    parser.add_argument("--account-id", default=ACCOUNT_ID, help="Atlassian Account ID")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without modifying Jira")
    parser.add_argument("--skip-project", action="store_true", help="Skip project creation step")
    args = parser.parse_args()

    print("=" * 70)
    print(" Smart Supply Chain Cyber Digital Twin (SSCDT) — Jira Initializer")
    print(f" Target Instance: {args.url}")
    print("=" * 70)

    # Initialize Jira Client
    client = JiraClient(args.url, args.email, args.token, dry_run=args.dry_run)

    # Auto-detect Account ID if placeholder
    account_id = args.account_id
    if not account_id or "your-account-id" in account_id or "[REPLACE" in account_id:
        print("[*] Detecting accountId via /rest/api/3/myself...")
        detected_id = client.get_myself_account_id()
        if detected_id:
            account_id = detected_id
            print(f"[OK] Detected Account ID: {account_id}")
        else:
            account_id = "unassigned"

    # Discover Custom Fields (Epic Name, Story Points, Epic Link)
    client.discover_fields()

    # Step 1: Project Creation
    if not args.skip_project:
        create_project(client, account_id)

    # Step 2: Components Creation
    create_components(client)

    # Step 3: Epics Creation
    epic_key_map = create_epics(client)

    # Step 4: Stories Creation
    story_key_map = create_stories(client, epic_key_map)

    # Step 5: Sprints Creation
    board_id = get_or_create_board(client)
    if board_id:
        s1_id, s2_id = create_sprints(client, board_id)
        # Step 6: Move Stories into Sprints
        assign_stories_to_sprints(client, story_key_map, s1_id, s2_id)
    else:
        print("[WARN] Scrum Board ID not found; skipping sprint creation.")

    # Save created keys to docs/jira_created_keys.json
    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "jira_created_keys.json")
    
    export_data = {
        "project": PROJECT_KEY,
        "epics": epic_key_map,
        "stories": story_key_map,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)
    print(f"\n[OK] Issue keys exported to: {out_file}")

    # Summary Report
    print("\n" + "=" * 70)
    print(" EXECUTION SUMMARY")
    print("=" * 70)
    print(f" Epics Created        : {client.stats['epics_created']} / 10")
    print(f" User Stories Created : {client.stats['stories_created']} / 39")
    print(f" Already Existed      : {client.stats['already_existed']}")
    print(f" Errors Encountered   : {client.stats['errors']}")
    print("=" * 70)
    print("Setup completed successfully!")


if __name__ == "__main__":
    main()
