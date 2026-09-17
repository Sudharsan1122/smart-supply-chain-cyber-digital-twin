# Deployment Guide — Smart Supply Chain Cyber Digital Twin

This guide provides comprehensive instructions for deploying the Smart Supply Chain Cyber Digital Twin across local development, containerized multi-service Docker Compose environments, and cloud targets.

---

## 1. Local Development (Virtual Environment)

### Prerequisites
- Python 3.13 (or 3.11+)
- Docker Desktop (for Postgres 16 and Mosquitto 2 dependencies)

### Steps

1. **Start Database and Message Broker**:
   ```bash
   docker compose up -d postgres mosquitto
   ```
   *Wait ~15 seconds for schema and seeds to initialize.*

2. **Set up Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```powershell
   Copy-Item .env.example .env
   ```

4. **Start FastAPI Backend**:
   ```powershell
   uvicorn api.app:app --reload --port 8000
   ```
   *Verify:* Navigate to `http://localhost:8000/docs`

5. **Start Flask Dashboard** (in another terminal):
   ```powershell
   .\venv\Scripts\Activate.ps1
   python -m flask --app dashboard.app run --port 5000
   ```
   *Verify:* Navigate to `http://localhost:5000`

---

## 2. Production Docker Compose (Full Stack)

To run the complete 4-service production stack:

```bash
# Build and launch all services in detached mode
docker compose up -d --build

# Inspect running containers
docker compose ps

# View unified application logs
docker compose logs -f api
```

### Services Started:
- `sscdt-postgres`: PostgreSQL 16 on port `5432` with persistent volume `pgdata`.
- `sscdt-mosquitto`: Eclipse Mosquitto on port `1883` (TCP) and `9001` (WebSockets).
- `sscdt-api`: FastAPI backend on port `8000`.
- `sscdt-dashboard`: Gunicorn-backed Flask dashboard on port `5000`.

---

## 3. Cloud Deployment (AWS & Terraform)

For production deployment onto AWS:
- **Database**: Amazon Aurora PostgreSQL Serverless v2 or RDS Multi-AZ.
- **Message Broker**: AWS IoT Core or Amazon MQ for RabbitMQ/MQTT.
- **Container Execution**: Amazon Elastic Container Service (ECS) with AWS Fargate, or Amazon Elastic Kubernetes Service (EKS).
- **Static Assets & Dashboard**: Application Load Balancer (ALB) routing `/api/*` to FastAPI and `/*` to the Flask UI.
- **Infrastructure as Code**: Terraform modules in `terraform/` manage VPC subnets, IAM roles with least privilege, security groups, and parameter stores.

---

## 4. Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `"Smart Supply Chain Cyber Digital Twin"` | Application title reported in health metadata. |
| `APP_VERSION` | `"1.0.0"` | Current release version string. |
| `ENVIRONMENT` | `DEBUG` / `PRODUCTION` | Runtime mode controlling logging and stack traces. |
| `DB_HOST` | `localhost` / `postgres` | Hostname or service name for PostgreSQL. |
| `DB_PORT` | `5432` | TCP port for PostgreSQL connection pool. |
| `DB_NAME` | `supply_chain_twin` | Target database catalog name. |
| `DB_USER` | `postgres` | Database username. |
| `DB_PASSWORD` | `postgres` | Database password. |
| `MQTT_BROKER_HOST`| `localhost` / `mosquitto` | Hostname for Mosquitto MQTT broker. |
| `MQTT_BROKER_PORT`| `1883` | TCP port for MQTT pub/sub listener. |
| `API_URL` | `http://localhost:8000` | Base URL used by dashboard to query API. |
| `VIRUSTOTAL_API_KEY` | `""` | Optional API key for VirusTotal IOC lookups. |
| `ABUSEIPDB_API_KEY` | `""` | Optional API key for AbuseIPDB IP reputation checks. |
| `ALIENVAULT_OTX_KEY`| `""` | Optional API key for AlienVault OTX pulses. |
| `RISK_SWEEP_INTERVAL_SECONDS` | `120` | Interval between automated graph risk recalculations. |
| `TRIAGE_TP_THRESHOLD` | `0.65` | Confidence cutoff score for True Positive triage verdicts. |

---

## 5. Troubleshooting & Common Issues

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Port 5432 conflict on host** | Local native Windows PostgreSQL service (`postgresql-x64-18`) is already bound to port 5432. | Stop the local Windows service or change port mapping in `.env` and `docker-compose.yml` to `5433:5432`. |
| **Database Password Auth Failed** | Stale Docker volume has old credentials from previous initialization. | Run `docker compose down -v` to purge volumes, then restart with `docker compose up -d`. |
| **Dashboard shows 0 assets** | Backend has not loaded state, or `.env` is missing / pointing to wrong DB host. | Verify `.env` exists (`Test-Path .env`), check `/api/ready`, and confirm 32 assets via `SELECT COUNT(*) FROM assets`. |
| **Ports 8000 or 5000 in use** | Lingering `uvicorn` or `flask` background process. | Run `Get-Process \| Where-Object { $_.ProcessName -match "uvicorn\|flask" } \| Stop-Process -Force`. |
| **ModuleNotFoundError** | Required packages not installed in active environment. | Run `pip install -r requirements.txt` followed by `pip install networkx scikit-learn joblib`. |
| **MQTT Connection Refused** | Mosquitto container not ready or port 1883 blocked by firewall. | Check `docker compose ps` to ensure mosquitto is running; verify `config/mosquitto.conf` has `allow_anonymous true`. |
