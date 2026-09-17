# Deployment Guide

## Local Development

### Prerequisites
- Docker Desktop
- Python 3.13
- Git

### Steps

```bash
# 1. Clone
git clone <your-repo-url>
cd smart-supply-chain-cyber-digital-twin

# 2. Create venv
python -m venv venv
.\venv\Scripts\Activate.ps1    # Windows
source venv/bin/activate       # macOS/Linux

# 3. Install deps
pip install -r requirements.txt

# 4. Copy env
Copy-Item .env.example .env    # Windows
cp .env.example .env           # Unix

# 5. Start infrastructure
docker compose up -d postgres mosquitto

# 6. Wait for DB seed
Start-Sleep -Seconds 15

# 7. Start API
uvicorn api.app:app --reload --port 8000

# 8. (new terminal) Start dashboard
python -m flask --app dashboard.app run --port 5000
