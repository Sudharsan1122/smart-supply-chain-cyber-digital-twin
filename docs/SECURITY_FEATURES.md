# Security Features Implemented

## 18 Security Layers

| # | Feature | Attack Addressed | Location |
|---|---------|------------------|----------|
| 1 | HTTPS/TLS | Eavesdropping, MITM | External API calls |
| 2 | Pydantic v2 validation | SQL injection, type confusion | api/schemas/ |
| 3 | Custom field validators | Path traversal | api/schemas/telemetry.py |
| 4 | SQLAlchemy ORM | SQL injection | database/repository.py |
| 5 | Secrets in .env | Credential leaks | .gitignore |
| 6 | Non-root containers | Privilege escalation | Dockerfiles |
| 7 | Docker network isolation | Lateral movement | docker-compose.yml |
| 8 | IOC allowlist filter | Internal IP leakage | attack_story/ioc_extractor.py |
| 9 | Rate limiting | DoS, API abuse | api_sources/base.py |
| 10 | JWT bearer tokens | Unauthorized access | Wazuh adapter |
| 11 | Timezone-aware datetime | Time attacks | All models |
| 12 | Pydantic strict mode | Mass assignment | All schemas |
| 13 | No eval/exec/pickle | RCE | Code review |
| 14 | HTTPS for external APIs | Data interception | All adapters |
| 15 | AWS Secrets Manager | Secret theft | terraform/ |
| 16 | Non-root DB user | DB privilege escalation | docker-compose.yml |
| 17 | Container healthchecks | DoS resilience | docker-compose.yml |
| 18 | Structured logging | Forensic analysis | Throughout |

## Attack Mapping (STRIDE)
| Layer | S | T | R | I | D | E |
|-------|---|---|---|---|---|---|
| HTTPS | ✅ | ✅ | | ✅ | | |
| Pydantic | | ✅ | | | | |
| ORM | | ✅ | | | | |
| .env | | | | ✅ | | |
| Non-root | | | | | | ✅ |
| Rate limit | | | | | ✅ | |
| JWT | ✅ | | | | | |
| Healthchecks | | | | | ✅ | |
