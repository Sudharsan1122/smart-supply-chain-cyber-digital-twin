# Smart Supply Chain Cyber Digital Twin

An API-first cyber-physical Digital Twin platform designed to secure, monitor, and analyze modern supply chains. The platform ingests telemetry and security events across a 32-node asset graph, tracks digital twin state, detects anomalies (both rule-based and machine-learning driven), runs simulated attack campaigns, performs blast radius and risk analyses, and triages threat intelligence.

---

## System Architecture & Stack

- **Backend API**: FastAPI (Python 3.13) + Pydantic v2 + SQLAlchemy (AsyncIO)
- **Database**: PostgreSQL 16 (Relational tables + 32 seeded supply chain assets)
- **Message Broker**: Eclipse Mosquitto MQTT for real-time telemetry streaming
- **Digital Twin Graph**: NetworkX DAG modeling dependencies, suppliers, warehouses, gateways, sensors, and servers
- **Detection & ML Engine**: Isolation Forest anomaly detection (scikit-learn) + correlation rules
- **Dashboard**: Flask + responsive UI (Live Fleet, Attack Stories, Threat Intel, and Triage Sweep)

---

## Quick Start

### 1. Prerequisites
- Docker Desktop (WSL2 backend on Windows)
- Python 3.11+ / 3.13+

### 2. Infrastructure Setup
Bring up PostgreSQL and Mosquitto MQTT:
```bash
docker compose up -d postgres mosquitto
```

### 3. Environment & Dependencies
```bash
# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows PowerShell
# source venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

Ensure `.env` exists (copied from `.env.example`):
```bash
cp .env.example .env
```

### 4. Run Backend & Dashboard

**FastAPI Backend** (Port 8000):
```bash
uvicorn api.app:app --reload --port 8000
```
- Swagger UI / OpenAPI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`
- Readiness check: `http://localhost:8000/api/ready`

**Flask Dashboard** (Port 5000):
```bash
python -m flask --app dashboard.app run --port 5000
```
- Live Fleet Dashboard: `http://localhost:5000`
- Attack Stories: `http://localhost:5000/stories`
- Threat Intelligence: `http://localhost:5000/threat-intel`
- Automated Triage: `http://localhost:5000/triage`

---

## End-to-End Simulation Demo

To fire simulated multi-stage attacks across vehicle gateways, warehouses, and authentication systems:
```bash
python -m demo.orchestrator
```
This orchestrates:
1. System readiness verification
2. Digital twin graph snapshot (32 nodes)
3. Simulated attack injections (`SIM-01`, `SIM-02`, `SIM-03`)
4. IOC extraction & Threat Intel enrichment
5. Attack story timeline synthesis
6. Incident triage scoring & risk propagation

---

## License
MIT License
