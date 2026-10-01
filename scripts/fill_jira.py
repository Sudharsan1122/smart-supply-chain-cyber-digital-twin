#!/usr/bin/env python3
"""
fill_jira.py — Fills existing Jira Scrum project SSCDT with:
  1. Dynamic field discovery (Story Points, Epic Link, Sprint, Epic Name)
  2. Verification of Scrum board ("SSCDT board")
  3. 39 User Stories with ADF descriptions, Story Points, Epic Links, Components, and Labels
  4. 2 Sprints with start/end dates
  5. Assignment of all 39 stories to Sprint 1 and Sprint 2
  6. Story Points estimation verification for Active Sprints & Burndown Chart
"""

import os
import sys
import json
import time
import base64
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import requests

# ============================================================
# CONFIG BLOCK
# ============================================================
JIRA_URL    = os.getenv("JIRA_BASE_URL", "https://mastersudhan1234.atlassian.net").rstrip("/")
EMAIL       = os.getenv("JIRA_USER_EMAIL", "mastersudhan1234@gmail.com")
API_TOKEN   = os.getenv("JIRA_API_TOKEN", "ATATT3xFfGF0mzIL7Fl3rw-1tSd_hSW-9xjQpXaEfq-C-eD4QY5nSTjTDRnX2WT7p4Y4ScacWOw1qpVdaTeFL7AXpKr5XbPWSx1lQmK3LX7Jag6QHlHAZBgek6h9w_tw7xKp0b8JT3-20WiBArZw3DyUMT0TFvfBtBN7kSWRL1LzMUuj7kRDp4Q=650A0802")
PROJECT_KEY = "SSCDT"
BOARD_NAME  = "SSCDT board"
ACCOUNT_ID  = os.getenv("JIRA_ACCOUNT_ID", "712020:3edf19c5-b975-470a-9e1f-bec93774ae4d")

# Pre-existing 10 Epics on Jira Cloud
EPIC_KEYS = {
    "EPIC-1":  "SSCDT-33",
    "EPIC-2":  "SSCDT-34",
    "EPIC-3":  "SSCDT-35",
    "EPIC-4":  "SSCDT-36",
    "EPIC-5":  "SSCDT-37",
    "EPIC-6":  "SSCDT-38",
    "EPIC-7":  "SSCDT-39",
    "EPIC-8":  "SSCDT-40",
    "EPIC-9":  "SSCDT-41",
    "EPIC-10": "SSCDT-42",
}

# Global Field IDs discovered dynamically in Step 0
SP_FIELD: Optional[str] = None
SP_ESTIMATE_FIELD: Optional[str] = None
EPIC_LINK_FIELD: Optional[str] = None
SPRINT_FIELD: Optional[str] = None
EPIC_NAME_FIELD: Optional[str] = None
BOARD_ID: Optional[int] = None
SPRINT_1_ID: Optional[int] = None
SPRINT_2_ID: Optional[int] = None

# ============================================================
# 39 USER STORIES SPECIFICATION
# ============================================================
STORIES_SPECS = [
    {
        "id": "US-01",
        "summary": "US-01: REST telemetry ingestion endpoint",
        "points": 5,
        "component": "Ingestion",
        "labels": ["phase-1"],
        "epic": "EPIC-1",
        "sprint": 1,
        "priority": "High",
        "role": "Ingestion Pipeline",
        "capability": "ingest raw asset telemetry payloads via REST /api/v1/telemetry",
        "benefit": "real-time sensor streams are validated with Pydantic and staged for twin processing",
        "ac": [
            "Given valid JSON telemetry payload with asset_id and metrics, When POST /api/v1/telemetry is received, Then HTTP 201 is returned and event is published to bus.",
            "Given invalid schema or missing timestamp, When POST /api/v1/telemetry is called, Then HTTP 422 Unprocessable Entity is returned with validation errors."
        ]
    },
    {
        "id": "US-02",
        "summary": "US-02: REST event ingestion endpoint",
        "points": 5,
        "component": "Ingestion",
        "labels": ["phase-5"],
        "epic": "EPIC-1",
        "sprint": 1,
        "priority": "High",
        "role": "SOC Operator",
        "capability": "ingest security events and alert triggers via REST /api/v1/events",
        "benefit": "discrete operational events are logged to PostgreSQL for correlation",
        "ac": [
            "Given an alert event payload from an edge gateway, When POST /api/v1/events is invoked, Then event is persisted to security_events table with unique UUID.",
            "Given high-severity event, When persisted, Then detection engine triggers immediate asset state evaluation."
        ]
    },
    {
        "id": "US-03",
        "summary": "US-03: MQTT bridge subscriber",
        "points": 8,
        "component": "Ingestion",
        "labels": ["phase-6"],
        "epic": "EPIC-1",
        "sprint": 1,
        "priority": "High",
        "role": "IoT Gateway",
        "capability": "subscribe to MQTT telemetry topics on Mosquitto broker (telemetry/#, alerts/#)",
        "benefit": "low-bandwidth field sensors transmit telemetry asynchronously over QoS 1",
        "ac": [
            "Given active Mosquitto broker, When truck IoT devices publish to telemetry/trucks/{id}, Then bridge consumes message and forwards to twin queue.",
            "Given broker disconnect, When connection is restored, Then bridge automatically reconnects with backoff and resumes subscription."
        ]
    },
    {
        "id": "US-04",
        "summary": "US-04: Wazuh SIEM integration",
        "points": 5,
        "component": "Ingestion",
        "labels": ["wazuh"],
        "epic": "EPIC-1",
        "sprint": 1,
        "priority": "Medium",
        "role": "Security Analyst",
        "capability": "ingest alerts and file integrity monitoring (FIM) events from Wazuh SIEM API",
        "benefit": "host-level intrusions and unauthorized file changes are unified into twin telemetry",
        "ac": [
            "Given Wazuh agent alert on logistics server, When polled by Wazuh forwarder, Then normalized alert is ingested into digital twin.",
            "Given rule ID match in 100000 series, When ingested, Then mapped to corresponding MITRE ATT&CK technique."
        ]
    },
    {
        "id": "US-05",
        "summary": "US-05: Suricata IDS integration",
        "points": 5,
        "component": "Ingestion",
        "labels": ["suricata"],
        "epic": "EPIC-1",
        "sprint": 1,
        "priority": "Medium",
        "role": "Network Defense Operator",
        "capability": "stream Suricata eve.json network IDS alert logs into twin pipeline",
        "benefit": "perimeter network anomalies, port scans, and malicious payloads are detected in real time",
        "ac": [
            "Given Suricata generates signature alert in eve.json, When parsed by file watcher, Then network alert is forwarded to correlation pipeline.",
            "Given external attacker IP in alert, When received, Then IOC is queued for live threat intelligence enrichment."
        ]
    },
    {
        "id": "US-06",
        "summary": "US-06: PostgreSQL schema (20 tables)",
        "points": 13,
        "component": "Ingestion",
        "labels": ["phase-2"],
        "epic": "EPIC-1",
        "sprint": 1,
        "priority": "High",
        "role": "Data Engineer",
        "capability": "deploy normalized PostgreSQL relational schema spanning 20 tables with 32 seeded supply chain assets",
        "benefit": "twin graph, telemetry history, IOC intelligence, and triage records maintain ACID integrity",
        "ac": [
            "Given fresh PostgreSQL instance, When Alembic migrations execute, Then all 20 tables and constraints are created.",
            "Given seed dataset, When initialization script executes, Then 32 assets across 4 tiers are seeded with baseline attributes."
        ]
    },
    {
        "id": "US-07",
        "summary": "US-07: NetworkX DiGraph twin",
        "points": 8,
        "component": "Digital Twin Core",
        "labels": ["phase-3"],
        "epic": "EPIC-2",
        "sprint": 1,
        "priority": "High",
        "role": "Twin Engine",
        "capability": "model the 32-asset supply chain topology as an in-memory directed graph (NetworkX DiGraph)",
        "benefit": "dependency paths, flow directions, and blast radius calculations execute with sub-millisecond latency",
        "ac": [
            "Given 32 assets and 14 dependency edges, When twin initializes, Then DiGraph is constructed with node attributes (risk, state, tier).",
            "Given asset failure or isolation, When graph topology changes, Then shortest paths and connectivity matrices update dynamically."
        ]
    },
    {
        "id": "US-08",
        "summary": "US-08: Live state manager",
        "points": 5,
        "component": "Digital Twin Core",
        "labels": ["phase-3"],
        "epic": "EPIC-2",
        "sprint": 1,
        "priority": "High",
        "role": "Twin Engine",
        "capability": "maintain real-time in-memory state dictionary for all 32 assets with atomic updates",
        "benefit": "subsystems read synchronized operational states without locking database records",
        "ac": [
            "Given incoming telemetry packet, When state manager processes update, Then asset current state and timestamp update atomically.",
            "Given concurrent readers, When state is queried, Then thread-safe non-blocking snapshot is returned."
        ]
    },
    {
        "id": "US-09",
        "summary": "US-09: Drift detection & auto-reconcile",
        "points": 5,
        "component": "Digital Twin Core",
        "labels": ["phase-8"],
        "epic": "EPIC-2",
        "sprint": 1,
        "priority": "Medium",
        "role": "Twin Auditor",
        "capability": "compare physical telemetry against digital twin model expectations to identify drift",
        "benefit": "silent sensor degradation or unauthorized device reprogramming is caught within 30 seconds",
        "ac": [
            "Given telemetry deviates >15% from twin model for 3 consecutive intervals, When drift check runs, Then DRIFT_DETECTED event is emitted.",
            "Given drift resolution signal, When auto-reconcile triggers, Then digital twin state synchronizes with physical baseline."
        ]
    },
    {
        "id": "US-10",
        "summary": "US-10: Time-travel snapshots",
        "points": 13,
        "component": "Digital Twin Core",
        "labels": ["phase-9"],
        "epic": "EPIC-2",
        "sprint": 1,
        "priority": "Medium",
        "role": "Forensic Investigator",
        "capability": "record periodic state snapshots allowing historical playback and time-travel querying",
        "benefit": "security analysts can replay cyber incidents step-by-step to understand propagation dynamics",
        "ac": [
            "Given continuous system execution, When 60-second snapshot timer fires, Then full twin state vector is saved with ISO timestamp.",
            "Given timestamp T, When GET /api/v1/twin/snapshot?time=T is called, Then graph and asset states at time T are reconstructed."
        ]
    },
    {
        "id": "US-11",
        "summary": "US-11: Eclipse Ditto integration",
        "points": 13,
        "component": "Digital Twin Core",
        "labels": ["eclipse-ditto"],
        "epic": "EPIC-2",
        "sprint": 1,
        "priority": "High",
        "role": "Digital Twin Architect",
        "capability": "mirror 32 supply chain entities as synchronized Things inside Eclipse Ditto via Ditto HTTP API",
        "benefit": "industry-standard digital twin protocol interoperability and state persistence are achieved",
        "ac": [
            "Given 32 physical assets, When Ditto syncer executes, Then 32 corresponding Things exist in Eclipse Ditto namespace org.sscdt.",
            "Given telemetry update, When PUT /api/2/things/{thingId}/features is executed, Then Ditto feature properties reflect live values."
        ]
    },
    {
        "id": "US-12",
        "summary": "US-12: 10 rule-based detectors",
        "points": 13,
        "component": "Detection Engine",
        "labels": ["phase-10"],
        "epic": "EPIC-3",
        "sprint": 1,
        "priority": "High",
        "role": "Detection Engineer",
        "capability": "implement 10 deterministic detection rules for sensor tampering, route deviation, and protocol abuse",
        "benefit": "known operational violations trigger zero-false-negative alerts instantly",
        "ac": [
            "Given GPS jump >500km/h or temperature > threshold, When evaluated by rule engine, Then ALERT_CRITICAL event is created.",
            "Given all 10 rules evaluated against test vectors, When executed, Then 100% of defined attack patterns trigger alert."
        ]
    },
    {
        "id": "US-13",
        "summary": "US-13: 9 asset-type state machines",
        "points": 8,
        "component": "Detection Engine",
        "labels": ["phase-11"],
        "epic": "EPIC-3",
        "sprint": 1,
        "priority": "High",
        "role": "Security Architect",
        "capability": "enforce 9 finite state machines (FSMs) for each asset class (truck, warehouse, gateway, etc.)",
        "benefit": "illegal state transitions (e.g., Transit -> Maintenance without Docking) are caught immediately",
        "ac": [
            "Given asset in state IDLE, When valid START_TRANSIT event occurs, Then state transitions to IN_TRANSIT.",
            "Given invalid transition event, When processed, Then transition is rejected and STATE_VIOLATION alert is logged."
        ]
    },
    {
        "id": "US-14",
        "summary": "US-14: 6 correlation rules",
        "points": 8,
        "component": "Detection Engine",
        "labels": ["phase-7"],
        "epic": "EPIC-3",
        "sprint": 1,
        "priority": "High",
        "role": "Correlation Specialist",
        "capability": "correlate multi-source events across 6 temporal correlation windows",
        "benefit": "complex multi-stage cyber attacks spanning host, network, and IoT are aggregated into unified incidents",
        "ac": [
            "Given Suricata port scan followed by Wazuh auth failure within 120s, When correlation window closes, Then MULTI_STAGE_ATTACK incident is raised.",
            "Given uncorrelated isolated events, When processed, Then events remain individual alerts without incident creation."
        ]
    },
    {
        "id": "US-15",
        "summary": "US-15: Risk scoring (6 components)",
        "points": 8,
        "component": "Detection Engine",
        "labels": ["phase-12"],
        "epic": "EPIC-3",
        "sprint": 1,
        "priority": "High",
        "role": "Risk Modeler",
        "capability": "compute composite asset risk score using 6 weighted components (CVSS, anomaly, drift, topology, C8, history)",
        "benefit": "operators receive normalized 0-100 risk values prioritizing critical infrastructure assets",
        "ac": [
            "Given asset telemetry and alert history, When risk computation executes, Then normalized score between 0.0 and 100.0 is generated.",
            "Given high threat-intel verdict (C8), When risk is calculated, Then asset risk increases proportionally to provider consensus."
        ]
    },
    {
        "id": "US-16",
        "summary": "US-16: IOC extraction (11 types)",
        "points": 8,
        "component": "Threat Intelligence",
        "labels": ["phase-15", "ioc"],
        "epic": "EPIC-4",
        "sprint": 2,
        "priority": "High",
        "role": "Threat Intel Analyst",
        "capability": "extract 11 distinct IOC types (IP, domain, SHA256, CVE, URL, email, etc.) from incoming alerts",
        "benefit": "security events are dissected into atomic indicators ready for threat intelligence lookups",
        "ac": [
            "Given security alert containing IPv4 address and SHA256 file hash, When extractor runs, Then both IOCs are extracted and typed.",
            "Given RFC 1918 private IP addresses, When parsed, Then internal IPs are filtered out from public threat lookups."
        ]
    },
    {
        "id": "US-17",
        "summary": "US-17: 3-provider enrichment",
        "points": 13,
        "component": "Threat Intelligence",
        "labels": ["phase-16"],
        "epic": "EPIC-4",
        "sprint": 2,
        "priority": "Highest",
        "role": "Threat Intel Analyst",
        "capability": "enrich extracted IOCs across 3 external threat feeds: VirusTotal, AbuseIPDB, and AlienVault OTX",
        "benefit": "threat indicators receive multi-source reputation scores and malicious consensus tagging",
        "ac": [
            "Given suspicious IP, When enriched against AbuseIPDB and AlienVault, Then reputation score and threat pulses are aggregated.",
            "Given API provider outage or rate limit, When fallback executes, Then cached reputation or neutral score is assigned."
        ]
    },
    {
        "id": "US-18",
        "summary": "US-18: C8 risk reweighting loop",
        "points": 13,
        "component": "Threat Intelligence",
        "labels": ["c8", "research"],
        "epic": "EPIC-4",
        "sprint": 2,
        "priority": "Highest",
        "role": "Research Scientist",
        "capability": "close feedback loop by reweighting asset risk scores based on live C8 threat-intel consensus",
        "benefit": "demonstrates core academic contribution C8: live external intelligence dynamically shifts twin risk posture",
        "ac": [
            "Given confirmed malicious verdict from 2+ threat providers, When C8 loop executes, Then connected asset risk score increases by reweight factor delta.",
            "Given reweighted asset, When blast radius executes, Then downstream dependency risk shifts visibly in twin graph."
        ]
    },
    {
        "id": "US-19",
        "summary": "US-19: Blast radius computation",
        "points": 8,
        "component": "Analysis & Triage",
        "labels": ["phase-17"],
        "epic": "EPIC-5",
        "sprint": 2,
        "priority": "High",
        "role": "SOC Analyst",
        "capability": "compute blast radius propagation using BFS traversal with 0.7^depth exponential decay",
        "benefit": "incident responders instantly visualize downstream supply chain disruption from a single compromised asset",
        "ac": [
            "Given compromised warehouse node at depth 0, When blast radius runs, Then depth 1 nodes receive 0.7 risk impact and depth 2 nodes receive 0.49 impact.",
            "Given isolated asset with no outgoing edges, When computed, Then blast radius contains only the seed asset."
        ]
    },
    {
        "id": "US-20",
        "summary": "US-20: Attack story engine",
        "points": 13,
        "component": "Analysis & Triage",
        "labels": ["phase-14", "mitre"],
        "epic": "EPIC-5",
        "sprint": 2,
        "priority": "High",
        "role": "SOC Analyst",
        "capability": "reconstruct chronological attack narratives mapped across 13 MITRE ATT&CK tactics",
        "benefit": "complex telemetry anomalies are converted into human-readable attack timelines for incident reports",
        "ac": [
            "Given sequence of correlated alerts on fleet gateway, When story engine runs, Then chronological narrative with MITRE technique IDs is output.",
            "Given MITRE ATT&CK tactic progression (Initial Access -> Lateral Movement -> Impact), When mapped, Then progression phases are highlighted."
        ]
    },
    {
        "id": "US-21",
        "summary": "US-21: Auto-triage classifier",
        "points": 8,
        "component": "Analysis & Triage",
        "labels": ["phase-18"],
        "epic": "EPIC-5",
        "sprint": 2,
        "priority": "High",
        "role": "SOC Team Lead",
        "capability": "automatically classify incident priority with verified performance metrics (P=0.89, R=1.00, F1=0.94)",
        "benefit": "eliminates alert fatigue by auto-escalating genuine threats while filtering benign sensor noise",
        "ac": [
            "Given incoming incident feature vector, When auto-triage model evaluates, Then priority classification (P1-Critical to P4-Low) is assigned.",
            "Given critical attack telemetry, When evaluated, Then model achieves 1.00 recall ensuring zero missed severe incidents."
        ]
    },
    {
        "id": "US-22",
        "summary": "US-22: XAI (SHAP) explanations",
        "points": 8,
        "component": "Analysis & Triage",
        "labels": ["xai"],
        "epic": "EPIC-5",
        "sprint": 2,
        "priority": "Medium",
        "role": "Compliance Auditor",
        "capability": "generate TreeSHAP feature importance plots and force explanations for ML-based triage decisions",
        "benefit": "analysts and academic reviewers understand exactly which features drove the automated classification",
        "ac": [
            "Given auto-triage decision, When XAI endpoint is queried, Then top-5 contributing features with positive/negative SHAP values are returned.",
            "Given explanation request in UI, When loaded, Then interactive waterfall/force visualization renders within 1 second."
        ]
    },
    {
        "id": "US-23",
        "summary": "US-23: 4-tab dashboard",
        "points": 13,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "epic": "EPIC-6",
        "sprint": 2,
        "priority": "High",
        "role": "SOC Operator",
        "capability": "navigate responsive 4-tab dashboard (Overview, Topology Graph, Incidents & Triage, C8 Threat Intel)",
        "benefit": "operators monitor entire 32-asset twin ecosystem from a centralized web console",
        "ac": [
            "Given active web browser, When dashboard URL is accessed, Then 4 tabs render with real-time SSE telemetry updates.",
            "Given tab switch, When clicked, Then sub-view renders without page reload."
        ]
    },
    {
        "id": "US-24",
        "summary": "US-24: Live geographic map",
        "points": 8,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "epic": "EPIC-6",
        "sprint": 2,
        "priority": "High",
        "role": "Logistics Dispatcher",
        "capability": "visualize transit fleet assets on interactive Leaflet map moving along real highway coordinates",
        "benefit": "real-time spatial tracking of shipping containers and vehicle health across Chennai transit routes",
        "ac": [
            "Given moving vehicle telemetry, When GPS coordinates update, Then truck marker animates along road polyline on Leaflet map.",
            "Given asset click, When marker selected, Then popup displays current speed, cargo temperature, and risk score."
        ]
    },
    {
        "id": "US-25",
        "summary": "US-25: Timeline playback",
        "points": 5,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "epic": "EPIC-6",
        "sprint": 2,
        "priority": "Medium",
        "role": "Security Researcher",
        "capability": "scrub through historical incident timeline with play, pause, and speed multiplier controls",
        "benefit": "facilitates live demonstration and retrospective incident drill-downs for stakeholders",
        "ac": [
            "Given past attack simulation, When user drags timeline slider, Then twin state and map markers reflect historical timestamp.",
            "Given Play clicked at 2x speed, When running, Then time advances smoothly at double real-time rate."
        ]
    },
    {
        "id": "US-26",
        "summary": "US-26: Geofencing + weather overlay",
        "points": 5,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "epic": "EPIC-6",
        "sprint": 2,
        "priority": "Medium",
        "role": "Logistics Security Manager",
        "capability": "render active geofencing boundaries and live OpenWeatherMap precipitation overlays on the map",
        "benefit": "distinguishes between route deviations caused by severe weather versus cyber-physical route hijacking",
        "ac": [
            "Given vehicle exits designated corridor polygon, When evaluated, Then GEOFENCE_BREACH alert is flagged in UI.",
            "Given live weather API enabled, When toggled, Then precipitation radar layer overlays accurately on map tiles."
        ]
    },
    {
        "id": "US-27",
        "summary": "US-27: Isolation Forest models (8)",
        "points": 8,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "epic": "EPIC-7",
        "sprint": 1,
        "priority": "High",
        "role": "ML Engineer",
        "capability": "train and serve 8 Isolation Forest models tuned for asset class telemetry feature distributions",
        "benefit": "unsupervised anomaly detection flags subtle multi-sensor deviations without requiring labeled attack data",
        "ac": [
            "Given baseline sensor telemetry dataset, When model training completes, Then serialized joblib models exist for each asset class.",
            "Given anomalous sensor combination, When evaluated, Then contamination score > 0.65 produces anomaly flag."
        ]
    },
    {
        "id": "US-28",
        "summary": "US-28: One-Class SVM models (8)",
        "points": 8,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "epic": "EPIC-7",
        "sprint": 1,
        "priority": "High",
        "role": "ML Engineer",
        "capability": "deploy 8 complementary One-Class SVM models with RBF kernel for non-linear boundary verification",
        "benefit": "ensemble detection with Isolation Forest reduces false positive rate to under 3.5%",
        "ac": [
            "Given normalized feature vectors, When scored against One-Class SVM decision boundary, Then outlier distance is returned.",
            "Given ensemble agreement (both IF + OCSVM flag anomaly), When evaluated, Then high-confidence ML_ANOMALY is emitted."
        ]
    },
    {
        "id": "US-29",
        "summary": "US-29: ML-ANOMALY detection wiring",
        "points": 5,
        "component": "Machine Learning",
        "labels": ["ml"],
        "epic": "EPIC-7",
        "sprint": 1,
        "priority": "High",
        "role": "Pipeline Architect",
        "capability": "wire real-time telemetry inference queue to scikit-learn models with sub-20ms inference latency",
        "benefit": "continuous machine learning evaluation without degrading ingestion throughput",
        "ac": [
            "Given batch of 50 sensor events, When evaluated by inference worker, Then total processing time is < 50ms.",
            "Given inference anomaly, When flagged, Then event is published directly to correlation engine."
        ]
    },
    {
        "id": "US-30",
        "summary": "US-30: Multi-stage Dockerfiles",
        "points": 8,
        "component": "Infrastructure & DevOps",
        "labels": ["docker", "phase-23"],
        "epic": "EPIC-8",
        "sprint": 2,
        "priority": "High",
        "role": "DevOps Engineer",
        "capability": "author hardened multi-stage Dockerfiles for backend API, dashboard, and ML inference services",
        "benefit": "minimal container image sizes, non-root user execution, and zero unnecessary build toolchains",
        "ac": [
            "Given docker build on api service, When build completes, Then final image runs as non-root user (UID 10001).",
            "Given vulnerability scan using Trivy, When scanned, Then zero CRITICAL or HIGH vulnerabilities exist in final layer."
        ]
    },
    {
        "id": "US-31",
        "summary": "US-31: Docker Compose (14 containers)",
        "points": 5,
        "component": "Infrastructure & DevOps",
        "labels": ["docker"],
        "epic": "EPIC-8",
        "sprint": 2,
        "priority": "High",
        "role": "DevOps Engineer",
        "capability": "orchestrate the full 14-container ecosystem via unified docker-compose.yml with healthchecks and networks",
        "benefit": "entire cyber digital twin stack starts deterministically with a single `docker compose up -d` command",
        "ac": [
            "Given docker compose up -d executed, When containers initialize, Then all 14 containers report 'healthy' status within 90s.",
            "Given network isolation, When tested, Then database and broker are not directly exposed to public WAN."
        ]
    },
    {
        "id": "US-32",
        "summary": "US-32: CI/CD pipeline",
        "points": 5,
        "component": "Infrastructure & DevOps",
        "labels": ["cicd"],
        "epic": "EPIC-8",
        "sprint": 2,
        "priority": "High",
        "role": "Automation Specialist",
        "capability": "configure GitHub Actions workflows for continuous integration (ci.yml) and automated staging deployment (deploy.yml)",
        "benefit": "automated linting, pytest suite execution, and security checks run on every pull request and push to main",
        "ac": [
            "Given git push to main, When GitHub Actions triggers, Then CI workflow runs pytest, flake8, and bandit with green pass status.",
            "Given pull request, When tests fail or coverage drops below 85%, Then PR merge is blocked."
        ]
    },
    {
        "id": "US-33",
        "summary": "US-33: AWS Terraform",
        "points": 21,
        "component": "Infrastructure & DevOps",
        "labels": ["terraform", "phase-24"],
        "epic": "EPIC-8",
        "sprint": 2,
        "priority": "Medium",
        "role": "Cloud Architect",
        "capability": "provision AWS ECS Fargate, RDS PostgreSQL, and ALB infrastructure via modular Terraform scripts",
        "benefit": "reproducible, infrastructure-as-code cloud deployment ready for enterprise-scale multi-region twin deployment",
        "ac": [
            "Given terraform plan executed, When evaluated, Then valid execution graph for VPC, ECS, and RDS is generated without syntax errors.",
            "Given terraform apply, When deployed, Then public HTTPS endpoint serves dashboard with automated TLS certificate."
        ]
    },
    {
        "id": "US-34",
        "summary": "US-34: STRIDE threat model",
        "points": 8,
        "component": "Security & Compliance",
        "labels": ["security"],
        "epic": "EPIC-9",
        "sprint": 2,
        "priority": "High",
        "role": "Security Engineer",
        "capability": "perform formal STRIDE threat modeling across all DFD Level 0, 1, and 2 digital twin data boundaries",
        "benefit": "systematically identifies spoofing, tampering, repudiation, info disclosure, DoS, and elevation risks",
        "ac": [
            "Given 6 DFD trust boundaries, When STRIDE analysis executes, Then comprehensive threat matrix is documented with mitigations.",
            "Given each identified threat, When reviewed, Then corresponding security requirement (SR1-SR20) is mapped."
        ]
    },
    {
        "id": "US-35",
        "summary": "US-35: 20 security requirements (SR1-SR20)",
        "points": 5,
        "component": "Security & Compliance",
        "labels": ["security"],
        "epic": "EPIC-9",
        "sprint": 2,
        "priority": "High",
        "role": "Compliance Officer",
        "capability": "specify, implement, and verify 20 security requirements covering authentication, encryption, and auditability",
        "benefit": "rigorous security posture verified for academic review and defense industry standards",
        "ac": [
            "Given SR1-SR20 specifications, When verified, Then every requirement has corresponding test case and implementation code.",
            "Given unauthenticated access attempt, When tested, Then JWT / mTLS authentication properly rejects request with HTTP 401."
        ]
    },
    {
        "id": "US-36",
        "summary": "US-36: Dependency reduction & audit",
        "points": 3,
        "component": "Security & Compliance",
        "labels": ["security"],
        "epic": "EPIC-9",
        "sprint": 2,
        "priority": "Medium",
        "role": "Software Architect",
        "capability": "audit all third-party Python packages using pip-audit and Safety to eliminate known CVEs",
        "benefit": "secures software supply chain against upstream library tampering and transitive vulnerabilities",
        "ac": [
            "Given pip-audit executed on requirements.txt, When scan runs, Then zero known vulnerabilities with fixable advisories are detected.",
            "Given lockfile generation, When pinned, Then all package hashes are cryptographically verified."
        ]
    },
    {
        "id": "US-37",
        "summary": "US-37: ~200 tests, >=85% coverage",
        "points": 13,
        "component": "Documentation",
        "labels": ["testing", "phase-21"],
        "epic": "EPIC-10",
        "sprint": 2,
        "priority": "High",
        "role": "QA Engineer",
        "capability": "author ~200 automated pytest unit, integration, and mock attack tests achieving >=85% test coverage",
        "benefit": "ensures system correctness across all 24 development phases with zero regressions during change management",
        "ac": [
            "Given pytest executed with pytest-cov, When test suite completes, Then all tests pass and branch coverage is >= 85%.",
            "Given simulated attack payloads, When passed to test suite, Then detection engines accurately flag violations."
        ]
    },
    {
        "id": "US-38",
        "summary": "US-38: 11 GitHub documents",
        "points": 8,
        "component": "Documentation",
        "labels": ["documentation"],
        "epic": "EPIC-10",
        "sprint": 2,
        "priority": "High",
        "role": "Technical Writer",
        "capability": "publish 11 comprehensive GitHub Markdown technical deliverables covering architecture, security, and operations",
        "benefit": "provides end-to-end documentation for project examiners, open-source contributors, and research reviewers",
        "ac": [
            "Given docs/ directory, When inspected, Then 11 technical documents (Requirements, Threat Model, Change Management, etc.) exist.",
            "Given internal file cross-references, When verified, Then all markdown links and PlantUML diagram assets resolve without 404s."
        ]
    },
    {
        "id": "US-39",
        "summary": "US-39: 53 requirements documented",
        "points": 8,
        "component": "Documentation",
        "labels": ["documentation"],
        "epic": "EPIC-10",
        "sprint": 2,
        "priority": "High",
        "role": "Lead Architect",
        "capability": "document all 53 formal project requirements (23 Functional, 10 Non-Functional, 20 Security Requirements)",
        "benefit": "ensures full traceability between IEEE software requirements engineering standards and Jira backlog issues",
        "ac": [
            "Given PHASE_1_REQUIREMENTS.md, When reviewed, Then 23 FRs, 10 NFRs, and 20 SRs are enumerated with rationale.",
            "Given Jira backlog, When cross-referenced, Then each requirement maps to corresponding user story and acceptance criteria."
        ]
    }
]


# ============================================================
# ADF (ATLASSIAN DOCUMENT FORMAT) BUILDER
# ============================================================
def make_adf_description(role: str, capability: str, benefit: str, ac_list: List[str]) -> Dict[str, Any]:
    """Generates a valid Jira Cloud ADF v1 JSON document with User Story + Acceptance Criteria."""
    ac_bullet_items = []
    for ac in ac_list:
        ac_bullet_items.append({
            "type": "listItem",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": ac}]
                }
            ]
        })

    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "User Story"}]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"As a {role}, I want {capability} so that {benefit}."}
                ]
            },
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Acceptance Criteria"}]
            },
            {
                "type": "bulletList",
                "content": ac_bullet_items
            }
        ]
    }


# ============================================================
# JIRA CLIENT CLASS
# ============================================================
class JiraClient:
    def __init__(self, base_url: str, email: str, token: str, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.token = token
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.auth = (self.email, self.token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self.stats = {
            "stories_created": 0,
            "stories_updated": 0,
            "sprint1_points": 0,
            "sprint2_points": 0,
            "errors": 0
        }

    def jira(self, method: str, path: str, json_data: Any = None, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Executes raw REST API calls using requests.Session with HTTP Basic Auth.
        Logs status, prints error text on failure without crashing, and returns parsed JSON or None.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        if self.dry_run:
            print(f"[DRY-RUN] {method.upper()} {url}")
            if json_data is not None:
                snippet = json.dumps(json_data, indent=2)[:300]
                print(f"          Payload: {snippet}...")
            return {}

        for attempt in range(1, 4):
            try:
                resp = self.session.request(method, url, json=json_data, **kwargs)
                if resp.status_code in (200, 201):
                    try:
                        return resp.json()
                    except Exception:
                        return {}
                elif resp.status_code == 204:
                    return {}
                else:
                    print(f"[!] {method.upper()} {path} -> HTTP {resp.status_code}")
                    try:
                        err_body = resp.json()
                        print(f"    Error details: {json.dumps(err_body)[:300]}")
                    except Exception:
                        print(f"    Response text: {resp.text[:250]}")
                    return None
            except Exception as exc:
                if attempt < 3:
                    print(f"[WARN] Connection to {url} failed ({exc}). Retrying attempt {attempt+1}/3 in 2s...")
                    time.sleep(2)
                else:
                    print(f"[ERROR] Connection to {url} failed after 3 attempts: {exc}")
                    self.stats["errors"] += 1
                    return None


# ============================================================
# STEP 0 — FIELD DISCOVERY
# ============================================================
def step0_discover_fields(client: JiraClient):
    """
    Step 0: Discovers Story Points, Epic Link, Sprint, and Epic Name field IDs.
    Queries GET /rest/api/3/field and board configuration.
    """
    global SP_FIELD, SP_ESTIMATE_FIELD, EPIC_LINK_FIELD, SPRINT_FIELD, EPIC_NAME_FIELD
    print("\n" + "=" * 60)
    print("STEP 0 — Field Discovery (GET /rest/api/3/field)")
    print("=" * 60)

    if client.dry_run:
        SP_FIELD = "customfield_10065"
        SP_ESTIMATE_FIELD = "customfield_10016"
        EPIC_LINK_FIELD = "customfield_10014"
        SPRINT_FIELD = "customfield_10020"
        EPIC_NAME_FIELD = "customfield_10011"
        print(f"  [DRY-RUN] Discovered fields:")
        print(f"    - Story Points field ID        : {SP_FIELD}")
        print(f"    - Story Point Estimate field ID: {SP_ESTIMATE_FIELD}")
        print(f"    - Epic Link field ID           : {EPIC_LINK_FIELD}")
        print(f"    - Sprint field ID              : {SPRINT_FIELD}")
        print(f"    - Epic Name field ID           : {EPIC_NAME_FIELD}")
        return

    fields = client.jira("GET", "/rest/api/3/field") or []
    for f in fields:
        fname = f.get("name", "").strip()
        fid = f.get("id", "")
        fl = fname.lower()

        # Prioritize exact "Story Points" over "Story point estimate"
        if fname == "Story Points":
            SP_FIELD = fid
        elif fl in ("story points", "story point estimate") and not SP_FIELD:
            SP_FIELD = fid
        
        if fl in ("story point estimate", "story-point-estimate"):
            SP_ESTIMATE_FIELD = fid

        if fl in ("epic link", "epic-link"):
            EPIC_LINK_FIELD = fid
        elif fl in ("sprint",):
            SPRINT_FIELD = fid
        elif fl in ("epic name", "epic-name"):
            EPIC_NAME_FIELD = fid

    # Fallback to standard Jira Cloud customfield defaults if not matched
    if not SP_FIELD:
        SP_FIELD = "customfield_10016"
    if not SP_ESTIMATE_FIELD:
        SP_ESTIMATE_FIELD = "customfield_10016"
    if not EPIC_LINK_FIELD:
        EPIC_LINK_FIELD = "customfield_10014"
    if not SPRINT_FIELD:
        SPRINT_FIELD = "customfield_10020"
    if not EPIC_NAME_FIELD:
        EPIC_NAME_FIELD = "customfield_10011"

    print("  [OK] Discovered custom field IDs:")
    print(f"    - 'Story Points' field ID        : {SP_FIELD}")
    print(f"    - 'Story point estimate' field ID: {SP_ESTIMATE_FIELD}")
    print(f"    - 'Epic Link' field ID           : {EPIC_LINK_FIELD}")
    print(f"    - 'Sprint' field ID              : {SPRINT_FIELD}")
    print(f"    - 'Epic Name' field ID           : {EPIC_NAME_FIELD}")


# ============================================================
# STEP 1 — VERIFY THE BOARD
# ============================================================
def step1_verify_board(client: JiraClient) -> Optional[int]:
    """
    Step 1: Queries GET /rest/agile/1.0/board?projectKeyOrId=SSCDT.
    Finds the board matching BOARD_NAME ("SSCDT board") and sets BOARD_ID.
    """
    global BOARD_ID
    print("\n" + "=" * 60)
    print(f"STEP 1 — Verify the Board ({BOARD_NAME})")
    print("=" * 60)

    if client.dry_run:
        BOARD_ID = 34
        print(f"  [DRY-RUN] Selected Board '{BOARD_NAME}' (ID: {BOARD_ID})")
        return BOARD_ID

    data = client.jira("GET", f"/rest/agile/1.0/board?projectKeyOrId={PROJECT_KEY}")
    boards = (data or {}).get("values", [])
    
    if not boards:
        print(f"  [!] No boards found for project '{PROJECT_KEY}'. Falling back to ID: 34.")
        BOARD_ID = 34
        return BOARD_ID

    print(f"  [*] Available boards for project {PROJECT_KEY}:")
    selected_id = None
    for b in boards:
        bid = b.get("id")
        bname = b.get("name")
        btype = b.get("type")
        print(f"      • Board ID {bid}: '{bname}' (Type: {btype})")
        if bname.strip().lower() == BOARD_NAME.strip().lower():
            selected_id = bid

    if selected_id is None and boards:
        selected_id = boards[0].get("id")

    BOARD_ID = selected_id or 34
    print(f"  [OK] Active Scrum Board ID set to: {BOARD_ID} ('{BOARD_NAME}')")

    # Confirm estimation field on this board
    b_cfg = client.jira("GET", f"/rest/agile/1.0/board/{BOARD_ID}/configuration")
    if b_cfg and "estimation" in b_cfg:
        est = b_cfg.get("estimation", {})
        est_fid = est.get("field", {}).get("fieldId")
        est_dname = est.get("field", {}).get("displayName")
        print(f"  [OK] Board estimation statistic: '{est_dname}' (field: {est_fid})")
        if est_fid:
            global SP_FIELD
            SP_FIELD = est_fid

    return BOARD_ID


# ============================================================
# STEP 2 — CREATE OR UPDATE 39 STORIES
# ============================================================
def step2_create_or_update_stories(client: JiraClient, skip_existing: bool = True) -> Dict[str, str]:
    """
    Step 2: Creates or updates the 39 user stories.
    Sets Story Points (for Burndown chart), Epic Link / parent, Component, Labels, and ADF description.
    """
    print("\n" + "=" * 60)
    print("STEP 2 — Create / Update 39 User Stories")
    print("=" * 60)

    story_key_map: Dict[str, str] = {}

    # Query existing stories in project via search/jql to maintain idempotency
    existing_issues: Dict[str, str] = {}
    if not client.dry_run:
        search_res = client.jira(
            "POST",
            "/rest/api/3/search/jql",
            json_data={
                "jql": f'project = "{PROJECT_KEY}" AND issuetype = "Story"',
                "maxResults": 150,
                "fields": ["summary", "key", SP_FIELD, SP_ESTIMATE_FIELD]
            }
        )
        if search_res:
            for iss in search_res.get("issues", []):
                s_text = iss.get("fields", {}).get("summary", "")
                k = iss.get("key", "")
                for st in STORIES_SPECS:
                    if st["id"] in s_text:
                        existing_issues[st["id"]] = k

    for idx, st in enumerate(STORIES_SPECS, start=1):
        st_id = st["id"]
        epic_key = EPIC_KEYS.get(st["epic"])
        points = st["points"]

        if skip_existing and st_id in existing_issues:
            curr_key = existing_issues[st_id]
            story_key_map[st_id] = curr_key
            print(f"  [=] {st_id} already exists as {curr_key}. Synchronizing Story Points ({points} pts)...")
            
            # Ensure estimation points are updated in both SP_FIELD and SP_ESTIMATE_FIELD
            if not client.dry_run:
                update_fields = {SP_FIELD: float(points)}
                if SP_ESTIMATE_FIELD and SP_ESTIMATE_FIELD != SP_FIELD:
                    update_fields[SP_ESTIMATE_FIELD] = float(points)
                client.jira("PUT", f"/rest/api/3/issue/{curr_key}", json_data={"fields": update_fields})
            
            client.stats["stories_updated"] += 1
            time.sleep(0.1)
            continue

        # Prepare payload for new Story
        issue_fields: Dict[str, Any] = {
            "project": {"key": PROJECT_KEY},
            "issuetype": {"name": "Story"},
            "summary": st["summary"],
            "description": make_adf_description(st["role"], st["capability"], st["benefit"], st["ac"]),
            "priority": {"name": st["priority"]},
            "labels": st["labels"],
            "components": [{"name": st["component"]}],
            SP_FIELD: float(points),
        }
        if SP_ESTIMATE_FIELD and SP_ESTIMATE_FIELD != SP_FIELD:
            issue_fields[SP_ESTIMATE_FIELD] = float(points)

        # Epic association: Modern Jira uses "parent", legacy uses customfield_10014
        if epic_key:
            if EPIC_LINK_FIELD:
                issue_fields[EPIC_LINK_FIELD] = epic_key
            else:
                issue_fields["parent"] = {"key": epic_key}

        if client.dry_run:
            mock_key = f"{PROJECT_KEY}-{idx + 42}"
            story_key_map[st_id] = mock_key
            print(f"  [DRY-RUN] [+] Create {st_id} ({points} pts) -> {mock_key} [Epic: {epic_key}]")
            client.stats["stories_created"] += 1
            continue

        resp = client.jira("POST", "/rest/api/3/issue", json_data={"fields": issue_fields})
        if resp and "key" in resp:
            new_key = resp["key"]
            story_key_map[st_id] = new_key
            client.stats["stories_created"] += 1
            print(f"  [+] Created {st_id} ({points} pts) -> {new_key} [Epic: {epic_key}]")
        else:
            # Fallback if epic_link failed: try parent
            if epic_key and EPIC_LINK_FIELD in issue_fields:
                issue_fields.pop(EPIC_LINK_FIELD, None)
                issue_fields["parent"] = {"key": epic_key}
                retry_resp = client.jira("POST", "/rest/api/3/issue", json_data={"fields": issue_fields})
                if retry_resp and "key" in retry_resp:
                    new_key = retry_resp["key"]
                    story_key_map[st_id] = new_key
                    client.stats["stories_created"] += 1
                    print(f"  [+] Created {st_id} (retry with parent) -> {new_key} [Epic: {epic_key}]")
                else:
                    client.stats["errors"] += 1
            else:
                client.stats["errors"] += 1

        time.sleep(0.35)

    return story_key_map


# ============================================================
# STEP 3 — CREATE 2 SPRINTS ON THE BOARD
# ============================================================
def step3_create_sprints(client: JiraClient, board_id: int) -> Tuple[Optional[int], Optional[int]]:
    """
    Step 3: Creates or reuses 2 sprints on the board.
    Sets start and end dates so sprints appear on Timeline and Burndown charts.
    """
    global SPRINT_1_ID, SPRINT_2_ID
    print("\n" + "=" * 60)
    print(f"STEP 3 — Create 2 Sprints on Board {board_id}")
    print("=" * 60)

    if client.dry_run:
        SPRINT_1_ID = 37
        SPRINT_2_ID = 38
        print(f"  [DRY-RUN] Sprint 1 ID: {SPRINT_1_ID}, Sprint 2 ID: {SPRINT_2_ID}")
        return SPRINT_1_ID, SPRINT_2_ID

    now = datetime.now(timezone.utc)
    s1_start = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    s1_end = (now + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    s2_start = (now + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    s2_end = (now + timedelta(days=28)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    sprint_configs = [
        {
            "num": 1,
            "name": "SSCDT Sprint 1: Foundation",  # <= 30 chars limit
            "goal": "Deliver ingestion, digital twin core, detection engine, and ML models (Epics 1, 2, 3, 7).",
            "startDate": s1_start,
            "endDate": s1_end,
            "state": "active"  # Active sprint enables Burndown Chart & Active Sprints board immediately
        },
        {
            "num": 2,
            "name": "SSCDT Sprint 2: Ops & Intel",
            "goal": "Deliver C8 threat intel, analysis/triage, dashboard, infra, security, testing, docs (Epics 4, 5, 6, 8, 9, 10).",
            "startDate": s2_start,
            "endDate": s2_end,
            "state": "future"
        }
    ]

    existing_sprints: Dict[str, int] = {}
    r = client.jira("GET", f"/rest/agile/1.0/board/{board_id}/sprint")
    if r:
        for sp in r.get("values", []):
            existing_sprints[sp.get("name")] = sp.get("id")

    sprint_ids = [None, None]

    for idx, scfg in enumerate(sprint_configs):
        sname = scfg["name"]
        sid = existing_sprints.get(sname)

        if sid:
            print(f"  [=] Sprint '{sname}' already exists (ID: {sid}). Updating dates & state...")
            sprint_ids[idx] = sid
            # Ensure dates and state are active/future
            client.jira("PUT", f"/rest/agile/1.0/sprint/{sid}", json_data={
                "name": sname,
                "state": scfg["state"],
                "startDate": scfg["startDate"],
                "endDate": scfg["endDate"],
                "goal": scfg["goal"]
            })
            continue

        payload = {
            "name": sname,
            "originBoardId": board_id,
            "goal": scfg["goal"],
            "startDate": scfg["startDate"],
            "endDate": scfg["endDate"]
        }
        res = client.jira("POST", "/rest/agile/1.0/sprint", json_data=payload)
        if res and "id" in res:
            created_sid = res["id"]
            sprint_ids[idx] = created_sid
            print(f"  [+] Created Sprint {scfg['num']}: '{sname}' (ID: {created_sid})")
            # Activate Sprint 1 if desired
            if scfg["state"] == "active":
                client.jira("PUT", f"/rest/agile/1.0/sprint/{created_sid}", json_data={
                    "name": sname,
                    "state": "active",
                    "startDate": scfg["startDate"],
                    "endDate": scfg["endDate"]
                })
        else:
            client.stats["errors"] += 1

    SPRINT_1_ID = sprint_ids[0]
    SPRINT_2_ID = sprint_ids[1]
    return SPRINT_1_ID, SPRINT_2_ID


# ============================================================
# STEP 4 — ASSIGN STORIES TO SPRINTS
# ============================================================
def step4_assign_stories_to_sprints(client: JiraClient, story_key_map: Dict[str, str], s1_id: Optional[int], s2_id: Optional[int]):
    """
    Step 4: Assigns the 39 user stories to Sprint 1 and Sprint 2 in batches of 50.
      Sprint 1: US-01..US-15, US-27, US-28, US-29 (18 stories)
      Sprint 2: US-16..US-26, US-30..US-39 (21 stories)
    """
    print("\n" + "=" * 60)
    print("STEP 4 — Assign Stories to Sprints")
    print("=" * 60)

    s1_keys: List[str] = []
    s2_keys: List[str] = []

    for st in STORIES_SPECS:
        k = story_key_map.get(st["id"])
        if not k:
            continue
        if st["sprint"] == 1:
            s1_keys.append(k)
        else:
            s2_keys.append(k)

    def batch_assign(sprint_id: Optional[int], keys: List[str], label: str):
        if not sprint_id or not keys:
            return
        print(f"[*] Moving {len(keys)} stories into {label} (ID: {sprint_id})...")
        # Batch in groups of 50
        batch_size = 50
        for i in range(0, len(keys), batch_size):
            chunk = keys[i:i + batch_size]
            if client.dry_run:
                print(f"  [DRY-RUN] Assigned batch of {len(chunk)} issues to {label}: {chunk[:5]}...")
                continue
            r = client.jira("POST", f"/rest/agile/1.0/sprint/{sprint_id}/issue", json_data={"issues": chunk})
            if r is not None:
                print(f"  [OK] Assigned {len(chunk)} issues to {label}.")
            else:
                client.stats["errors"] += 1

    batch_assign(s1_id, s1_keys, "Sprint 1")
    batch_assign(s2_id, s2_keys, "Sprint 2")


# ============================================================
# STEP 5 — VERIFY & SUMMARY
# ============================================================
def step5_verify_and_summarize(client: JiraClient, story_key_map: Dict[str, str], s1_id: Optional[int], s2_id: Optional[int]):
    """
    Step 5: Verifies story points in each sprint, writes docs/jira_created_keys.json,
    and prints execution summary.
    """
    print("\n" + "=" * 60)
    print("STEP 5 — Verification & Sprint Points Computation")
    print("=" * 60)

    s1_pts = 0.0
    s2_pts = 0.0

    if not client.dry_run:
        # Sum Sprint 1 Points
        if s1_id:
            s1_issues_data = client.jira("GET", f"/rest/agile/1.0/sprint/{s1_id}/issue?fields={SP_FIELD},{SP_ESTIMATE_FIELD}")
            if s1_issues_data:
                for iss in s1_issues_data.get("issues", []):
                    f = iss.get("fields", {})
                    pt = f.get(SP_FIELD) or f.get(SP_ESTIMATE_FIELD) or 0
                    try:
                        s1_pts += float(pt)
                    except (ValueError, TypeError):
                        pass

        # Sum Sprint 2 Points
        if s2_id:
            s2_issues_data = client.jira("GET", f"/rest/agile/1.0/sprint/{s2_id}/issue?fields={SP_FIELD},{SP_ESTIMATE_FIELD}")
            if s2_issues_data:
                for iss in s2_issues_data.get("issues", []):
                    f = iss.get("fields", {})
                    pt = f.get(SP_FIELD) or f.get(SP_ESTIMATE_FIELD) or 0
                    try:
                        s2_pts += float(pt)
                    except (ValueError, TypeError):
                        pass
    else:
        # Dry-run fallback sum from spec
        for st in STORIES_SPECS:
            if st["sprint"] == 1:
                s1_pts += st["points"]
            else:
                s2_pts += st["points"]

    client.stats["sprint1_points"] = int(s1_pts)
    client.stats["sprint2_points"] = int(s2_pts)

    # Export mapping to docs/jira_created_keys.json
    out_dir = Path(__file__).resolve().parent.parent / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "jira_created_keys.json"

    export_payload = {
        "project": PROJECT_KEY,
        "board_id": BOARD_ID,
        "sprint_1_id": s1_id,
        "sprint_2_id": s2_id,
        "epics": EPIC_KEYS,
        "stories": story_key_map,
        "summary": {
            "stories_total": len(story_key_map),
            "sprint1_points": client.stats["sprint1_points"],
            "sprint2_points": client.stats["sprint2_points"],
            "total_points": client.stats["sprint1_points"] + client.stats["sprint2_points"]
        },
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(export_payload, f, indent=2)
        print(f"  [OK] Saved issue key mapping to: {out_file}")
    except Exception as e:
        print(f"  [!] Failed to save export json: {e}")

    # Final summary output
    summary_report = {
        "project": PROJECT_KEY,
        "stories_created": client.stats["stories_created"],
        "stories_updated": client.stats["stories_updated"],
        "total_stories": len(story_key_map),
        "sprint_1_points": client.stats["sprint1_points"],
        "sprint_2_points": client.stats["sprint2_points"],
        "total_story_points": client.stats["sprint1_points"] + client.stats["sprint2_points"],
        "errors": client.stats["errors"]
    }

    print("\n" + "=" * 60)
    print("FINAL EXECUTION SUMMARY")
    print("=" * 60)
    print(f"  • Stories Created      : {summary_report['stories_created']}")
    print(f"  • Stories Synchronized : {summary_report['stories_updated']}")
    print(f"  • Total Active Stories : {summary_report['total_stories']} / 39")
    print(f"  • Sprint 1 Points      : {summary_report['sprint_1_points']} SP")
    print(f"  • Sprint 2 Points      : {summary_report['sprint_2_points']} SP")
    print(f"  • Total Project Points : {summary_report['total_story_points']} SP")
    print(f"  • Errors Encountered   : {summary_report['errors']}")
    print("=" * 60)
    print("\nFinal JSON Output:")
    print(json.dumps(summary_report, indent=2))


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Fill existing SSCDT Jira board with stories, estimation, and sprints")
    parser.add_argument("--url", default=JIRA_URL, help="Jira base URL")
    parser.add_argument("--email", default=EMAIL, help="Jira account email")
    parser.add_argument("--token", default=API_TOKEN, help="Jira API token")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without executing")
    parser.add_argument("--skip-existing", action="store_true", default=True, help="Skip creating existing issues and synchronize estimation")
    args = parser.parse_args()

    print("=" * 70)
    print(" SSCDT Jira Board Populator & Burndown Synchronizer")
    print(f" Target URL : {args.url}")
    print(f" Project Key: {PROJECT_KEY} | Board: {BOARD_NAME}")
    print("=" * 70)

    client = JiraClient(args.url, args.email, args.token, dry_run=args.dry_run)

    # STEP 0: Discover Fields
    step0_discover_fields(client)

    # STEP 1: Verify the Board
    board_id = step1_verify_board(client)
    if not board_id:
        print("[FATAL] Board could not be verified. Aborting.")
        sys.exit(1)

    # STEP 2: Create / Synchronize 39 Stories
    story_key_map = step2_create_or_update_stories(client, skip_existing=args.skip_existing)

    # STEP 3: Create / Configure Sprints (with start/end dates & active state)
    s1_id, s2_id = step3_create_sprints(client, board_id)

    # STEP 4: Assign Stories to Sprints
    step4_assign_stories_to_sprints(client, story_key_map, s1_id, s2_id)

    # STEP 5: Verify & Report
    step5_verify_and_summarize(client, story_key_map, s1_id, s2_id)


if __name__ == "__main__":
    main()
