#!/usr/bin/env python3
"""
setup_jira.py — Automated Jira Scrum Project Initializer for SSCDT
Smart Supply Chain Cyber Digital Twin (20CYS495 Project Phase-I)
Institution: Amrita Vishwa Vidyapeetham, Chennai
Team: Sudharsan S (Lead), Manojkumar A
Guide: Dr. S. Udhayakumar

Usage:
  python setup_jira.py --help
  python setup_jira.py --dry-run
  python setup_jira.py --url https://your-domain.atlassian.net --email user@example.com --token API_TOKEN
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional
import httpx

PROJECT_KEY = "SSCDT"
PROJECT_NAME = "Smart Supply Chain Cyber Digital Twin"
PROJECT_LEAD = "Sudharsan S"

COMPONENTS = [
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

EPICS = [
    {
        "key_id": 1,
        "name": "Ingestion & Data Layer",
        "summary": "Ingestion & Data Layer",
        "description": "Accept telemetry and security events from REST, MQTT, Wazuh SIEM, Suricata IDS, and external threat feeds. Persist records to PostgreSQL 16 across 20 relational tables for 32 seeded supply chain assets. Covers FR1–FR5 and Phases 1, 2, 4, 5, 6.",
        "component": "Ingestion",
        "labels": ["phase-1", "phase-2", "wazuh", "suricata"],
        "priority": "High",
    },
    {
        "key_id": 2,
        "name": "Digital Twin Core",
        "summary": "Digital Twin Core",
        "description": "Maintain a live digital twin network using NetworkX DiGraph (32 nodes, 14 edges), track real-time asset states, detect drift with auto-reconciliation, integrate Eclipse Ditto W3C Thing model (32 synced assets), and capture time-travel snapshots (full + delta). Covers FR6–FR9 and Phases 3, 8, 9, 20.",
        "component": "Digital Twin Core",
        "labels": ["phase-3", "eclipse-ditto"],
        "priority": "High",
    },
    {
        "key_id": 3,
        "name": "Detection Engine",
        "summary": "Detection Engine",
        "description": "Execute 10 rule-based anomaly detectors (RULE-001..RULE-010), 9 asset-type finite state machines, 6 multi-signal correlation rules, and 6-component dynamic risk scoring. Covers FR10–FR12 and Phases 7, 10, 11, 12.",
        "component": "Detection Engine",
        "labels": ["phase-1", "ml"],
        "priority": "High",
    },
    {
        "key_id": 4,
        "name": "Threat Intelligence (C8)",
        "summary": "Threat Intelligence (C8)",
        "description": "Extract 11 Indicator of Compromise (IOC) types, query VirusTotal, AbuseIPDB, and AlienVault OTX with 24h TTL cache, synthesize consensus reputation verdicts, and execute the closed-loop C8 risk reweighting loop. Covers FR13–FR15 and Phases 15, 16.",
        "component": "Threat Intelligence",
        "labels": ["c8", "ioc", "research"],
        "priority": "Highest",
    },
    {
        "key_id": 5,
        "name": "Analysis & Triage",
        "summary": "Analysis & Triage",
        "description": "Compute multi-hop blast radius using BFS traversal with 0.7^depth decay, reconstruct multi-stage attack stories mapped to 13 MITRE ATT&CK tactics, execute automated triage (TP/FP/FN/TN), and compute KernelSHAP explainability attributions. Covers FR16–FR18 and Phases 14, 17, 18, 22.",
        "component": "Analysis & Triage",
        "labels": ["mitre", "xai"],
        "priority": "Highest",
    },
    {
        "key_id": 6,
        "name": "Dashboard & Visualization",
        "summary": "Dashboard & Visualization",
        "description": "Deliver responsive web UI (Flask, Chart.js, D3 force graph, Leaflet India map), live fleet tracking along realistic highway corridors, timeline scrubber playback, Haversine geofence breach rings, and live weather overlay. Covers FR19–FR23 and Phase 19.",
        "component": "Dashboard & UI",
        "labels": ["phase-1", "phase-2"],
        "priority": "High",
    },
    {
        "key_id": 7,
        "name": "Machine Learning",
        "summary": "Machine Learning",
        "description": "Train 16 unsupervised ML models (8 Isolation Forest + 8 One-Class SVM) tailored per supply chain asset type, integrate ML-ANOMALY detection into triage, and extract KernelSHAP explanations. Covers Phase 22.",
        "component": "Machine Learning",
        "labels": ["ml", "xai"],
        "priority": "High",
    },
    {
        "key_id": 8,
        "name": "Infrastructure & DevOps",
        "summary": "Infrastructure & DevOps",
        "description": "Containerize platform across 14 Docker services, establish multi-stage Dockerfiles with non-root security, configure GitHub Actions CI/CD pipelines, and provide AWS Terraform infrastructure. Covers Phases 23, 24.",
        "component": "Infrastructure & DevOps",
        "labels": ["docker", "terraform"],
        "priority": "Medium",
    },
    {
        "key_id": 9,
        "name": "Security & Compliance",
        "summary": "Security & Compliance",
        "description": "Implement 20 defense-in-depth security requirements (SR1–SR20), STRIDE threat model, Wazuh HIDS + Suricata NIDS event ingestion, secure coding standards, and dependency audit reduction.",
        "component": "Security & Compliance",
        "labels": ["wazuh", "suricata"],
        "priority": "Medium",
    },
    {
        "key_id": 10,
        "name": "Testing & Documentation",
        "summary": "Testing & Documentation",
        "description": "Provide ~200 automated unit/integration tests with >=85% coverage via pytest, comprehensive software requirements specification (53 requirements), and 11 GitHub architectural documents. Covers Phase 21.",
        "component": "Documentation",
        "labels": ["testing", "documentation"],
        "priority": "Medium",
    },
]

STORIES = [
    # Epic 1: Ingestion & Data Layer
    {
        "id": "US-01",
        "summary": "REST telemetry ingestion endpoint",
        "description": "As a cyber-physical system, I want a POST /api/telemetry endpoint so external IoT sensors and gateways can stream real-time telemetry into the digital twin.",
        "ac": "Given valid telemetry JSON payload, When POSTed to /api/telemetry, Then return 201 Created and persist metric rows to PostgreSQL.",
        "points": 5,
        "epic_idx": 1,
        "component": "Ingestion",
        "labels": ["phase-1"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-02",
        "summary": "REST event ingestion endpoint",
        "description": "As a security operator, I want a POST /api/events endpoint so external security systems and edge gateways can push security event logs.",
        "ac": "Given a valid security event payload, When POSTed to /api/events, Then return 201 Created and trigger correlation.",
        "points": 5,
        "epic_idx": 1,
        "component": "Ingestion",
        "labels": ["phase-5"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-03",
        "summary": "MQTT bridge subscriber",
        "description": "As an IoT telemetry listener, I want an MQTT subscriber on supply_chain/telemetry/+ so high-frequency sensor messages are automatically ingested into the pipeline.",
        "ac": "Given MQTT messages published to broker, When received on subscribed topics, Then validate schema and ingest asynchronously.",
        "points": 8,
        "epic_idx": 1,
        "component": "Ingestion",
        "labels": ["phase-6"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-04",
        "summary": "Wazuh SIEM integration",
        "description": "As a SOC analyst, I want to pull host-based intrusion alerts from Wazuh Manager so endpoint compromises are reflected in the twin.",
        "ac": "Given Wazuh Manager API active, When alert events are generated, Then pull alerts via REST and map to twin asset IDs.",
        "points": 5,
        "epic_idx": 1,
        "component": "Ingestion",
        "labels": ["wazuh", "phase-1"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-05",
        "summary": "Suricata IDS integration",
        "description": "As a network security engineer, I want to read Suricata NIDS eve.json alerts so network-level anomalies are ingested into the twin.",
        "ac": "Given Suricata logging to eve.json, When network attacks occur, Then stream log records into ingestion pipeline.",
        "points": 5,
        "epic_idx": 1,
        "component": "Ingestion",
        "labels": ["suricata", "phase-1"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-06",
        "summary": "PostgreSQL schema (20 tables)",
        "description": "As a data architect, I want a normalized PostgreSQL schema with 20 tables and 32 seeded supply chain assets so that state and telemetry are durably stored.",
        "ac": "Given PostgreSQL 16 container, When schema and seed scripts execute, Then 20 tables and 32 assets are initialized.",
        "points": 13,
        "epic_idx": 1,
        "component": "Ingestion",
        "labels": ["phase-2"],
        "priority": "High",
        "sprint": 1,
    },
    # Epic 2: Digital Twin Core
    {
        "id": "US-07",
        "summary": "NetworkX DiGraph twin",
        "description": "As a digital twin engineer, I want a directed dependency graph representing 32 assets and 14 operational edges so that parent-child relationships and centralities are modeled.",
        "ac": "Given seeded assets in DB, When twin_graph initializes, Then 32 nodes and 14 edges are loaded with degree and betweenness centralities.",
        "points": 8,
        "epic_idx": 2,
        "component": "Digital Twin Core",
        "labels": ["phase-3"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-08",
        "summary": "Live state manager",
        "description": "As an operations engineer, I want real-time asset state tracking so that the twin reflects current operational and security health.",
        "ac": "Given incoming telemetry, When processed by normalizer, Then update in-memory twin_state and persist transitions.",
        "points": 5,
        "epic_idx": 2,
        "component": "Digital Twin Core",
        "labels": ["phase-8"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-09",
        "summary": "Drift detection & auto-reconcile",
        "description": "As a system maintainer, I want periodic drift detection every 30s so that in-memory twin state and database records stay reconciled.",
        "ac": "Given divergence between cache and database, When drift audit sweep runs, Then auto-reconcile state and log discrepancies.",
        "points": 5,
        "epic_idx": 2,
        "component": "Digital Twin Core",
        "labels": ["phase-8"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-10",
        "summary": "Time-travel snapshots",
        "description": "As a forensic investigator, I want full and delta state snapshots so that historical supply chain states can be reconstructed at any timestamp.",
        "ac": "Given historical state transitions, When requesting snapshot at timestamp T, Then reconstruct exact 32-asset state.",
        "points": 13,
        "epic_idx": 2,
        "component": "Digital Twin Core",
        "labels": ["phase-9"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-11",
        "summary": "Eclipse Ditto integration",
        "description": "As an enterprise architect, I want full Eclipse Ditto digital twin integration with 32 synchronized Things and a dashboard badge so that the platform conforms to W3C standards.",
        "ac": "Given 5 Ditto containers running, When ditto_sync executes every 5s, Then all 32 assets sync to /api/2/things and dashboard displays Ditto badge.",
        "points": 13,
        "epic_idx": 2,
        "component": "Digital Twin Core",
        "labels": ["eclipse-ditto"],
        "priority": "Highest",
        "sprint": 1,
    },
    # Epic 3: Detection Engine
    {
        "id": "US-12",
        "summary": "10 rule-based detectors",
        "description": "As a detection engineer, I want 10 deterministic detection rules (RULE-001..010) covering cold-chain, speed, geofencing, and brute-force so that known attack patterns are flagged.",
        "ac": "Given telemetry and event streams, When matching rule condition occurs, Then generate detection with confidence 0.60–0.95.",
        "points": 13,
        "epic_idx": 3,
        "component": "Detection Engine",
        "labels": ["phase-10"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-13",
        "summary": "9 asset-type state machines",
        "description": "As a security architect, I want finite state machines for all 9 asset types so that unauthorized or out-of-order state transitions are flagged as anomalies.",
        "ac": "Given asset state change, When transition violates defined lifecycle, Then emit transition anomaly detection.",
        "points": 8,
        "epic_idx": 3,
        "component": "Detection Engine",
        "labels": ["phase-11"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-14",
        "summary": "6 correlation rules",
        "description": "As an incident responder, I want 6 multi-signal correlation rules so that related alerts across temporal windows are grouped into actionable incidents.",
        "ac": "Given related detections within sliding window, When correlation conditions met, Then synthesize single consolidated incident.",
        "points": 8,
        "epic_idx": 3,
        "component": "Detection Engine",
        "labels": ["phase-7"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-15",
        "summary": "Risk scoring (6 components)",
        "description": "As a risk analyst, I want a 6-component dynamic risk scoring model (Detections 35%, Transitions 15%, Incidents 20%, Threat Intel 15%, Centrality 10%, Health 5%) so that asset risk is recomputed on every ingest.",
        "ac": "Given asset telemetry and detections, When scoring function evaluates, Then output normalized composite risk score 0–100.",
        "points": 8,
        "epic_idx": 3,
        "component": "Detection Engine",
        "labels": ["phase-12"],
        "priority": "High",
        "sprint": 1,
    },
    # Epic 4: Threat Intelligence (C8)
    {
        "id": "US-16",
        "summary": "IOC extraction (11 types)",
        "description": "As a threat researcher, I want automated extraction of 11 IOC types (IP, IPv6, domain, URL, MD5, SHA1, SHA256, email, MQTT topic, BTC, ETH) from raw payloads.",
        "ac": "Given abnormal payload, When regex parser executes, Then extract deduplicated IOCs and associate with asset.",
        "points": 8,
        "epic_idx": 4,
        "component": "Threat Intelligence",
        "labels": ["phase-15", "ioc"],
        "priority": "High",
        "sprint": 2,
    },
    {
        "id": "US-17",
        "summary": "3-provider enrichment",
        "description": "As a cyber threat analyst, I want automated threat intel lookups across VirusTotal, AbuseIPDB, and AlienVault OTX with 24h caching so that IOC reputation is established.",
        "ac": "Given extracted public IOC, When enrichment pipeline queries APIs, Then cache consensus verdict for 24 hours.",
        "points": 13,
        "epic_idx": 4,
        "component": "Threat Intelligence",
        "labels": ["phase-16"],
        "priority": "High",
        "sprint": 2,
    },
    {
        "id": "US-18",
        "summary": "C8 risk reweighting loop",
        "description": "As a cybersecurity researcher, I want the C8 dynamic risk reweighting loop so that malicious external threat intelligence automatically amplifies asset risk scores.",
        "ac": "Given malicious IOC verdict, When reweighting algorithm runs, Then amplify asset risk score and update downstream blast radius.",
        "points": 13,
        "epic_idx": 4,
        "component": "Threat Intelligence",
        "labels": ["c8", "research"],
        "priority": "Highest",
        "sprint": 2,
    },
    # Epic 5: Analysis & Triage
    {
        "id": "US-19",
        "summary": "Blast radius computation",
        "description": "As a SOC analyst, I want breadth-first topological blast radius computation with 0.7^depth distance attenuation so that cascade impact is quantified.",
        "ac": "Given compromised root asset, When BFS traversal executes up to depth 4, Then return list of impacted assets and scores.",
        "points": 8,
        "epic_idx": 5,
        "component": "Analysis & Triage",
        "labels": ["phase-17"],
        "priority": "High",
        "sprint": 2,
    },
    {
        "id": "US-20",
        "summary": "Attack story engine",
        "description": "As an incident commander, I want an attack storytelling engine that reconstructs chronological timelines and maps events to 13 MITRE ATT&CK tactics.",
        "ac": "Given multi-stage attack events, When narrative synthesizer runs, Then produce chronological story with MITRE tactics.",
        "points": 13,
        "epic_idx": 5,
        "component": "Analysis & Triage",
        "labels": ["phase-14", "mitre"],
        "priority": "High",
        "sprint": 2,
    },
    {
        "id": "US-21",
        "summary": "Auto-triage classifier",
        "description": "As a SOC lead, I want automated alert triage classifying detections as TP/FP/FN/TN with measured performance (P=0.89, R=1.00, F1=0.94) so that alert fatigue is eliminated.",
        "ac": "Given unclassified detections, When triage classifier executes, Then output classification metrics and confusion matrix.",
        "points": 8,
        "epic_idx": 5,
        "component": "Analysis & Triage",
        "labels": ["phase-18"],
        "priority": "Highest",
        "sprint": 2,
    },
    {
        "id": "US-22",
        "summary": "XAI (SHAP) explanations",
        "description": "As a security analyst, I want KernelSHAP feature attribution explanations for ML anomaly detections so that model predictions are transparent and explainable.",
        "ac": "Given ML anomaly alert, When /api/ml/explain/{id} is queried, Then return top-5 contributing features and attribution weights.",
        "points": 8,
        "epic_idx": 5,
        "component": "Analysis & Triage",
        "labels": ["xai"],
        "priority": "High",
        "sprint": 2,
    },
    # Epic 6: Dashboard & Visualization
    {
        "id": "US-23",
        "summary": "4-tab dashboard",
        "description": "As a security operator, I want a responsive 4-tab Flask dashboard (Live Fleet, Attack Stories, Threat Intel, Triage) with live 3-second auto-refresh.",
        "ac": "Given browser at http://localhost:5000, When navigating tabs, Then render responsive Chart.js and D3 views with live data.",
        "points": 13,
        "epic_idx": 6,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "sprint": 2,
    },
    {
        "id": "US-24",
        "summary": "Live geographic map",
        "description": "As a logistics security manager, I want a Leaflet map showing truck fleets traveling along real Indian highway corridors with marker clustering.",
        "ac": "Given truck GPS coordinates, When map loads, Then render trucks on OpenStreetMap with route trails and tooltips.",
        "points": 8,
        "epic_idx": 6,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "sprint": 2,
    },
    {
        "id": "US-25",
        "summary": "Timeline playback",
        "description": "As a security trainer, I want a historical timeline scrubber to rewind and replay attack simulations step-by-step.",
        "ac": "Given attack scenario execution, When moving timeline slider, Then rewind map and asset state to selected step.",
        "points": 5,
        "epic_idx": 6,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "sprint": 2,
    },
    {
        "id": "US-26",
        "summary": "Geofencing + weather overlay",
        "description": "As a fleet controller, I want Haversine geofence breach circles and live OpenWeather overlays displayed directly on the geographic map.",
        "ac": "Given truck coordinates and weather API, When rendering map, Then show colored geofence boundaries and cloud/temp layers.",
        "points": 5,
        "epic_idx": 6,
        "component": "Dashboard & UI",
        "labels": ["phase-19"],
        "priority": "High",
        "sprint": 2,
    },
    # Epic 7: Machine Learning
    {
        "id": "US-27",
        "summary": "Isolation Forest models (8)",
        "description": "As an ML engineer, I want 8 Isolation Forest anomaly detection models trained per asset type to detect zero-day telemetry anomalies.",
        "ac": "Given baseline telemetry training sets, When models train, Then persist artifacts in ml/artifacts/ with decision thresholds.",
        "points": 8,
        "epic_idx": 7,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-28",
        "summary": "One-Class SVM models (8)",
        "description": "As an ML engineer, I want 8 One-Class SVM models trained per asset type to provide complementary boundary-based anomaly detection.",
        "ac": "Given normal telemetry features, When SVM models fit, Then persist model weights and evaluate anomaly boundary.",
        "points": 8,
        "epic_idx": 7,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "priority": "High",
        "sprint": 1,
    },
    {
        "id": "US-29",
        "summary": "ML-ANOMALY detection wiring",
        "description": "As a pipeline developer, I want ML model inference integrated directly into the ingestion pipeline so that anomalous payloads trigger ML detections.",
        "ac": "Given incoming telemetry vector, When scored by trained models, Then emit ML-ANOMALY detection if threshold exceeded.",
        "points": 5,
        "epic_idx": 7,
        "component": "Machine Learning",
        "labels": ["ml", "phase-22"],
        "priority": "High",
        "sprint": 1,
    },
    # Epic 8: Infrastructure & DevOps
    {
        "id": "US-30",
        "summary": "Multi-stage Dockerfiles",
        "description": "As a DevOps engineer, I want optimized multi-stage Dockerfiles with non-root app users and healthchecks for secure container deployments.",
        "ac": "Given project repository, When docker build runs, Then produce minimal, non-root OCI-compliant container images.",
        "points": 8,
        "epic_idx": 8,
        "component": "Infrastructure & DevOps",
        "labels": ["docker", "phase-23"],
        "priority": "Medium",
        "sprint": 2,
    },
    {
        "id": "US-31",
        "summary": "Docker Compose (14 containers)",
        "description": "As a deployment engineer, I want a complete docker-compose.yml file orchestrating all 14 containers (API, DB, MQTT, Ditto, Wazuh, Suricata).",
        "ac": "Given docker compose up -d, When executed on host, Then all 14 services start healthy and interconnected.",
        "points": 5,
        "epic_idx": 8,
        "component": "Infrastructure & DevOps",
        "labels": ["docker", "phase-23"],
        "priority": "Medium",
        "sprint": 2,
    },
    {
        "id": "US-32",
        "summary": "CI/CD pipeline",
        "description": "As a software release engineer, I want automated GitHub Actions workflows running linting, tests, security audits, and container publishing.",
        "ac": "Given git push to main, When workflow triggers, Then execute pytest, coverage, Bandit SAST, and Docker build.",
        "points": 5,
        "epic_idx": 8,
        "component": "Infrastructure & DevOps",
        "labels": ["phase-23"],
        "priority": "Medium",
        "sprint": 2,
    },
    {
        "id": "US-33",
        "summary": "AWS Terraform",
        "description": "As a cloud architect, I want modular Terraform scripts deploying VPC, RDS Postgres, ECS Fargate, ALB, ECR, and Secrets Manager on AWS.",
        "ac": "Given terraform apply, When executed in cloud environment, Then provision production-ready supply chain twin infrastructure.",
        "points": 21,
        "epic_idx": 8,
        "component": "Infrastructure & DevOps",
        "labels": ["terraform", "phase-24"],
        "priority": "Medium",
        "sprint": 2,
    },
    # Epic 9: Security & Compliance
    {
        "id": "US-34",
        "summary": "STRIDE threat model",
        "description": "As a security architect, I want a comprehensive STRIDE threat model covering all DFD elements and trust boundaries with documented mitigations.",
        "ac": "Given 7-layer architecture, When STRIDE analysis evaluates components, Then document threats and verify mitigations in THREAT_MODEL.md.",
        "points": 8,
        "epic_idx": 9,
        "component": "Security & Compliance",
        "labels": ["phase-1"],
        "priority": "Medium",
        "sprint": 2,
    },
    {
        "id": "US-35",
        "summary": "20 security requirements (SR1–SR20)",
        "description": "As a compliance officer, I want all 20 security requirements implemented and documented across authentication, validation, and container isolation.",
        "ac": "Given system codebase, When auditing security layers, Then confirm all 20 requirements active and documented.",
        "points": 5,
        "epic_idx": 9,
        "component": "Security & Compliance",
        "labels": ["phase-1"],
        "priority": "Medium",
        "sprint": 2,
    },
    {
        "id": "US-36",
        "summary": "Dependency reduction & audit",
        "description": "As a DevSecOps specialist, I want automated dependency vulnerability scanning using Bandit, pip-audit, and safety with a clean bill of health.",
        "ac": "Given python dependencies, When pip-audit and bandit execute, Then report 0 known vulnerabilities and zero code smells.",
        "points": 3,
        "epic_idx": 9,
        "component": "Security & Compliance",
        "labels": ["phase-1"],
        "priority": "Medium",
        "sprint": 2,
    },
    # Epic 10: Testing & Documentation
    {
        "id": "US-37",
        "summary": "~200 tests, ≥85% coverage",
        "description": "As a QA lead, I want ~200 unit and integration tests achieving >=85% code coverage executed through pytest with XML reporting.",
        "ac": "Given pytest testpaths=tests, When test runner executes, Then all ~200 tests pass with coverage >= 85%.",
        "points": 13,
        "epic_idx": 10,
        "component": "Documentation",
        "labels": ["testing", "phase-21"],
        "priority": "Medium",
        "sprint": 2,
    },
    {
        "id": "US-38",
        "summary": "11 GitHub documents",
        "description": "As a technical writer, I want 11 comprehensive GitHub documentation files covering Architecture, API, Deployment, CICD, Requirements, and Diagrams.",
        "ac": "Given docs directory, When reviewing documentation, Then verify all 11 core markdown documents are complete and linked.",
        "points": 8,
        "epic_idx": 10,
        "component": "Documentation",
        "labels": ["documentation"],
        "priority": "Medium",
        "sprint": 2,
    },
    {
        "id": "US-39",
        "summary": "53 requirements documented",
        "description": "As a systems engineer, I want the complete Phase 1 Requirements document (23 FR, 10 NFR, 20 SR) published in docs/PHASE_1_REQUIREMENTS.md.",
        "ac": "Given Phase 1 deliverable guidelines, When compiling requirements, Then produce structured SRS document with 53 requirements.",
        "points": 8,
        "epic_idx": 10,
        "component": "Documentation",
        "labels": ["documentation", "phase-1"],
        "priority": "Medium",
        "sprint": 2,
    },
]


def create_jira_entities(base_url: str, email: str, token: str, dry_run: bool = False):
    auth = (email, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    print(f"[*] Initializing Jira Scrum Project setup for '{PROJECT_NAME}' ({PROJECT_KEY})...")
    if dry_run:
        print("[DRY-RUN] Simulating execution without calling Jira REST API.")
        print(f"  - 10 Components: {', '.join(COMPONENTS)}")
        print(f"  - 10 Epics: {len(EPICS)} epics prepared.")
        print(f"  - 39 User Stories: {len(STORIES)} stories prepared.")
        print("  - 2 Sprints: Sprint 1 (143 pts), Sprint 2 (186 pts).")
        return

    with httpx.Client(base_url=base_url, auth=auth, headers=headers, timeout=30.0) as client:
        # 1. Verify Project
        r = client.get(f"/rest/api/3/project/{PROJECT_KEY}")
        if r.status_code == 200:
            print(f"[OK] Project {PROJECT_KEY} exists.")
        else:
            print(f"[!] Project {PROJECT_KEY} not found (HTTP {r.status_code}). Please ensure project {PROJECT_KEY} is created as a Scrum Software project.")

        # 2. Components
        print("\n[*] Creating Components...")
        for comp in COMPONENTS:
            payload = {"name": comp, "project": PROJECT_KEY}
            cr = client.post("/rest/api/3/component", json=payload)
            if cr.status_code in (200, 201):
                print(f"  [+] Created component: {comp}")
            elif cr.status_code == 409 or "already exists" in cr.text.lower():
                print(f"  [=] Component already exists: {comp}")
            else:
                print(f"  [!] Component {comp} status {cr.status_code}: {cr.text[:100]}")

        # 3. Create Epics
        print("\n[*] Creating Epics...")
        epic_keys = {}
        for epic in EPICS:
            issue_payload = {
                "fields": {
                    "project": {"key": PROJECT_KEY},
                    "summary": f"EPIC-{epic['key_id']}: {epic['name']}",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": epic["description"]}],
                            }
                        ],
                    },
                    "issuetype": {"name": "Epic"},
                    "components": [{"name": epic["component"]}],
                    "labels": epic["labels"],
                    "priority": {"name": epic["priority"]},
                }
            }
            er = client.post("/rest/api/3/issue", json=issue_payload)
            if er.status_code in (200, 201):
                created_key = er.json()["key"]
                epic_keys[epic["key_id"]] = created_key
                print(f"  [+] Created Epic {epic['key_id']} -> {created_key}")
            else:
                print(f"  [!] Failed to create Epic {epic['key_id']}: {er.text[:150]}")
                epic_keys[epic["key_id"]] = f"{PROJECT_KEY}-{epic['key_id']}"

        # 4. Create User Stories
        print("\n[*] Creating 39 User Stories...")
        for story in STORIES:
            desc_text = f"{story['description']}\n\nAcceptance Criteria:\n{story['ac']}"
            parent_epic = epic_keys.get(story["epic_idx"], f"{PROJECT_KEY}-{story['epic_idx']}")
            story_payload = {
                "fields": {
                    "project": {"key": PROJECT_KEY},
                    "summary": f"{story['id']}: {story['summary']}",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": desc_text}],
                            }
                        ],
                    },
                    "issuetype": {"name": "Story"},
                    "parent": {"key": parent_epic},
                    "components": [{"name": story["component"]}],
                    "labels": story["labels"],
                    "priority": {"name": story["priority"]},
                }
            }
            sr = client.post("/rest/api/3/issue", json=story_payload)
            if sr.status_code in (200, 201):
                skey = sr.json()["key"]
                print(f"  [+] Created {story['id']} ({story['points']} pts) -> {skey} [Epic: {parent_epic}]")
            else:
                print(f"  [!] Failed {story['id']}: {sr.text[:150]}")

    print("\n[OK] Jira initialization complete!")


def main():
    parser = argparse.ArgumentParser(description="Initialize Jira Scrum Project for SSCDT")
    parser.add_argument("--url", default=os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net"), help="Jira base URL")
    parser.add_argument("--email", default=os.getenv("JIRA_USER_EMAIL", ""), help="Jira user email")
    parser.add_argument("--token", default=os.getenv("JIRA_API_TOKEN", ""), help="Jira API token")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without calling API")
    args = parser.parse_args()

    if not args.dry_run and (not args.email or not args.token):
        print("[INFO] No API credentials supplied. Running in --dry-run mode by default.")
        args.dry_run = True

    create_jira_entities(args.url, args.email, args.token, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
