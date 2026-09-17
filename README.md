# Smart Supply Chain Cyber Digital Twin

[![CI Pipeline](https://github.com/USER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/ci.yml)
[![Deploy Pipeline](https://github.com/USER/REPO/actions/workflows/deploy.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)

> **Note:** Replace `USER/REPO` in the badge links above with your GitHub username and repository name (e.g. `Sudharsan1122/smart-supply-chain-cyber-digital-twin`).

An API-first cyber-physical Digital Twin platform designed to monitor, simulate, and secure distributed supply chain infrastructure. Synchronizing real-time telemetry from 32 physical and logical assets into a directed dependency graph, the system continuously runs hybrid anomaly detection (rule-based + unsupervised Isolation Forest ML), models attack blast radii, enriches threat intelligence indicators, and automates incident triage.

---

## 🚀 Quick Start (Docker)

Launch the full production stack (FastAPI, Flask Dashboard, PostgreSQL 16, and Mosquitto MQTT) with a single command:

```bash
# Clone the repository
git clone https://github.com/Sudharsan1122/smart-supply-chain-cyber-digital-twin.git
cd smart-supply-chain-cyber-digital-twin

# Build and run the multi-container stack
docker compose up -d --build
```

Access the services:
- **Live Fleet Dashboard**: [http://localhost:5000](http://localhost:5000)
- **FastAPI Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **System Readiness Probe**: [http://localhost:8000/api/ready](http://localhost:8000/api/ready)

---

## 🛠️ Quick Start (Development Mode)

For local code editing and debugging:

```powershell
# 1. Start database and MQTT broker
docker compose up -d postgres mosquitto

# 2. Set up Python 3.13 virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Initialize environment variables
Copy-Item .env.example .env

# 4. Start the FastAPI backend
uvicorn api.app:app --reload --port 8000

# 5. In a second terminal, start the Flask dashboard
python -m flask --app dashboard.app run --port 5000
```

---

## 🎬 End-to-End Simulation Demo

Run the automated orchestrator to simulate multi-stage attack campaigns targeting vehicle gateways, warehouses, and identity servers:

```powershell
python -m demo.orchestrator
```

The orchestrator executes:
1. **Readiness Probe**: Verifies database, MQTT broker, and twin graph connectivity.
2. **Topology Snapshot**: Captures 32 assets and dependency edges.
3. **Attack Campaigns**: Injects `SIM-01` (Vehicle Gateway Compromise), `SIM-02` (Warehouse IoT Compromise), and `SIM-03` (Credential Anomaly).
4. **Threat Intelligence Enrichment**: Enriches extracted IOCs with external reputation feeds.
5. **Attack Story Synthesis**: Maps actions against MITRE ATT&CK tactics and generates incident narratives.
6. **Automated Triage Sweep**: Runs ML classifier evaluating true positive rates and updates dynamic risk scores.

---

## 🏛️ System Architecture

| Component | Technology | Role |
| :--- | :--- | :--- |
| **API Backend** | FastAPI (Python 3.13) + Pydantic v2 | High-performance async REST API and lifecycle management |
| **Database** | PostgreSQL 16 (Timescale/relational) | 20 schema tables for state, telemetry, IOCs, and triage |
| **Telemetry Bus** | Eclipse Mosquitto (MQTT 2.0) | Pub/Sub broker for real-time sensor streams |
| **Graph Model** | NetworkX | Directed Acyclic Graph (DAG) for dependency analysis & centrality |
| **ML Engine** | scikit-learn (Isolation Forest) | Unsupervised time-series anomaly detection |
| **Threat Intel** | VirusTotal, AbuseIPDB, AlienVault OTX | Dynamic reputation scoring and IOC enrichment |
| **Dashboard** | Flask + Jinja2 + CSS Grid | Responsive real-time UI with live auto-refreshing telemetry |

---

## 📚 Project Documentation

| Document | Description |
| :--- | :--- |
| [**Architecture Guide**](docs/ARCHITECTURE.md) | Full pipeline diagram, component breakdown, 10-step data flow, and 20 database tables. |
| [**Deployment Guide**](docs/DEPLOYMENT.md) | Local venv, Docker Compose stack, AWS cloud guide, configuration variables, and troubleshooting. |
| [**API Reference**](docs/API.md) | Comprehensive endpoint reference across all 14 API functional groups. |
| [**CI/CD Pipeline**](docs/CICD.md) | GitHub Actions workflow design, test automation, and container image publishing to GHCR. |

---

## 📂 Project Structure

```text
smart-supply-chain-cyber-digital-twin/
├── .github/workflows/          # CI/CD pipelines (test & deploy)
│   ├── ci.yml
│   └── deploy.yml
├── api/                        # FastAPI application & route controllers
│   ├── routes/                 # 14 distinct API feature routers
│   └── schemas/                # Pydantic data validation schemas
├── api_sources/                # Threat intel adapters (VirusTotal, AbuseIPDB)
├── attack_story/               # Story generation, MITRE tactics, timeline
├── config/                     # Pydantic configuration & Mosquitto settings
├── dashboard/                  # Flask web dashboard UI
│   ├── static/css/ & js/       # Responsive styles and live polling scripts
│   └── templates/              # Jinja2 templates (live, stories, triage, intel)
├── database/                   # SQLAlchemy async models & SQL seed files
│   ├── schema.sql              # 20 relational database tables
│   └── seed*.sql               # 32 seeded assets & attack scenarios
├── demo/                       # End-to-end simulation orchestrator
├── detection/                  # Dual-engine rules and risk scoring
├── digital_twin/               # NetworkX graph topology and state synchronization
├── docs/                       # Project documentation
├── ingestion/                  # MQTT broker listener and validation pipeline
├── ml/                         # Isolation Forest models and feature extractors
├── tests/                      # Automated pytest unit and integration test suite
├── Dockerfile                  # Multi-stage production API image
├── docker-compose.yml          # Complete 4-service production stack
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation index
```

---

## 🧪 Testing

Run the automated test suite locally:

```powershell
pytest tests/
```

---

## 🔄 CI/CD Automation

- **Continuous Integration (`ci.yml`)**: Triggered on pull requests and pushes to `main`, `master`, and `develop`. Tests database seeding, verifies 32 assets, runs pytest, checks live endpoints, and validates container builds.
- **Continuous Deployment (`deploy.yml`)**: Triggered on push to `main`. Builds and pushes multi-stage container images to GitHub Container Registry (`ghcr.io`).

---

## 💻 Tech Stack

- **Python 3.13**, **FastAPI**, **Flask**, **Gunicorn**, **Uvicorn**
- **PostgreSQL 16**, **SQLAlchemy 2.0 (AsyncIO)**, **asyncpg**
- **Eclipse Mosquitto 2.0**, **paho-mqtt**
- **NetworkX**, **scikit-learn**, **joblib**, **NumPy**, **Pandas**
- **Docker**, **Docker Compose**, **GitHub Actions**, **GHCR**

---

## 📄 License

Distributed under the [MIT License](LICENSE).
