# Baseline (v1.0.0) — Before CR-001

- Commit:      `f975425a3407ef36ef700c7e55cf015601ac9015` (`f975425`)
- Date:        2026-09-30
- Branch:      `main`

## Test Metrics
- Tests passing: 15 (8 core + 7 partner scaffold)
- Coverage:      97%

## Security Metrics
- Bandit HIGH:   0
- Bandit MEDIUM: 0
- Bandit LOW:    0
- pip-audit vulnerabilities: 0

## Module List
```text
backend/app/celery_app.py
backend/app/config.py
backend/app/constants.py
backend/app/database.py
backend/app/digital_twin/event_trigger.py
backend/app/digital_twin/sync_engine.py
backend/app/digital_twin/twin_manager.py
backend/app/exceptions.py
backend/app/main.py
backend/app/models.py
backend/app/optimization/scenarios.py
backend/app/optimization/solver.py
backend/app/optimization/storage_interface.py
backend/app/routers/audit.py
backend/app/routers/auth.py
backend/app/routers/optimization.py
backend/app/routers/partner.py
backend/app/routers/simulation.py
backend/app/routers/twin.py
backend/app/schemas.py
backend/app/security.py
backend/app/services/audit_service.py
backend/app/services/db_service.py
backend/app/services/notification_service.py
backend/app/services/partner_service.py
backend/app/simulation/runner.py
```

## CI/CD Status
- `ci.yml`:     passing
- `deploy.yml`: passing
