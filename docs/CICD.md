# CI/CD Pipeline Overview — Smart Supply Chain Cyber Digital Twin

This project utilizes automated GitHub Actions workflows to validate code changes and continuously publish production container images.

---

## Workflows Overview

The continuous delivery pipeline consists of two workflows located in `.github/workflows/`:

1. **Continuous Integration (`ci.yml`)**: Runs on every commit and pull request across `main`, `master`, and `develop` branches.
2. **Continuous Deployment (`deploy.yml`)**: Automatically packages and publishes multi-architecture OCI container images to the GitHub Container Registry (`ghcr.io`) upon pushing to `main`.

---

## 1. CI Workflow (`.github/workflows/ci.yml`)

### Triggers
- Push events to `main`, `master`, or `develop`.
- Pull Requests targeting `main`, `master`, or `develop`.

### Execution Steps
1. **Service Orchestration**: Spins up isolated PostgreSQL 16 (Alpine) with health probes and Mosquitto 2 MQTT containers.
2. **Repository Checkout**: Pulls repository code with submodules.
3. **Mosquitto Configuration**: Injects custom `mosquitto.conf` supporting anonymous local telemetry.
4. **Python 3.13 Setup**: Configures the Python 3.13 runtime with pip package caching.
5. **Dependency Installation**: Upgrades pip and installs `requirements.txt` along with testing dependencies.
6. **Database Schema & Seed Execution**: Applies `database/schema.sql`, `database/seed.sql`, and `database/seed_attacks.sql`.
7. **Asset Verification**: Asserts that `SELECT COUNT(*) FROM assets` equals exactly 32.
8. **Module Import Sanity Check**: Verifies that `api.app`, `dashboard.app`, `digital_twin.graph`, and `detection.engine` load cleanly without missing symbols.
9. **Automated Unit Tests**: Runs pytest across `tests/` verifying graph algorithms and settings.
10. **Backend Live Probe**: Starts Uvicorn in the background and asserts both `/api/health` and `/api/ready` return HTTP 200 with all dependencies connected.
11. **Container Build Validation**: Executes `docker build` against the multi-stage `Dockerfile`.

---

## 2. Deploy Workflow (`.github/workflows/deploy.yml`)

### Triggers
- Direct push or merged Pull Requests on the `main` branch.

### Execution Steps
1. **Buildx Initialization**: Sets up `docker/setup-buildx-action@v3` for optimized caching.
2. **Registry Authentication**: Logs in to GitHub Container Registry (`ghcr.io`) using temporary `$GITHUB_TOKEN`.
3. **API Image Publication**:
   - Builds `Dockerfile` targeting the FastAPI backend.
   - Pushes tags: `ghcr.io/<OWNER>/sscdt-api:latest` and `ghcr.io/<OWNER>/sscdt-api:<COMMIT_SHA>`.
4. **Dashboard Image Publication**:
   - Builds `dashboard/Dockerfile` targeting the Gunicorn Flask UI.
   - Pushes tags: `ghcr.io/<OWNER>/sscdt-dashboard:latest` and `ghcr.io/<OWNER>/sscdt-dashboard:<COMMIT_SHA>`.

---

## 3. Local CI Simulation

You can simulate the CI workflow locally on Windows PowerShell before pushing:

```powershell
# 1. Start clean Postgres and Mosquitto services
docker compose down -v
docker compose up -d postgres mosquitto
Start-Sleep -Seconds 10

# 2. Verify seeded assets count
docker exec sscdt-postgres psql -U postgres -d supply_chain_twin -c "SELECT COUNT(*) FROM assets;"

# 3. Test python imports
.\venv\Scripts\python.exe -c "import api.app; import dashboard.app; print('Imports OK')"

# 4. Run pytest test suite
.\venv\Scripts\pytest.exe tests/

# 5. Build Docker images locally
docker build -t sscdt-api:local .
docker build -f dashboard/Dockerfile -t sscdt-dashboard:local .
```

---

## 4. Status Badges

Add these status badges to the top of your `README.md` (replace `USER/REPO` with your repository path):

```markdown
[![CI Pipeline](https://github.com/USER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/ci.yml)
[![Deploy Pipeline](https://github.com/USER/REPO/actions/workflows/deploy.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
```
