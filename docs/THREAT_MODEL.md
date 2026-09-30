# STRIDE Threat Model — Smart Supply Chain Cyber Digital Twin

## System Overview
32-asset supply chain digital twin with 7-layer architecture.

## STRIDE Analysis

### S — Spoofing
**Threat:** Attacker impersonates a truck gateway (VGW-101)
**Impact:** Unauthorized telemetry injection
**Mitigation:** RULE-007 firmware validation, JWT auth for Wazuh

### T — Tampering
**Threat:** Modify telemetry in transit
**Impact:** False readings, corrupted twin state
**Mitigation:** HTTPS/TLS, Pydantic v2 validation, IOC allowlist

### R — Repudiation
**Threat:** Deny sending malicious payload
**Impact:** No accountability
**Mitigation:** Structured logging, timestamped audit trail

### I — Information Disclosure
**Threat:** Steal API keys from `.env`
**Impact:** Abuse of VirusTotal/AbuseIPDB quotas
**Mitigation:** `.gitignore`, AWS Secrets Manager, non-root containers

### D — Denial of Service
**Threat:** Flood `/api/telemetry` endpoint
**Impact:** Service unavailable
**Mitigation:** Rate limiting, Docker healthchecks, resource limits

### E — Elevation of Privilege
**Threat:** Container escape to root
**Impact:** Full system control
**Mitigation:** Non-root `USER app`, Docker network isolation

## Threat Matrix

| Component | STRIDE | Risk | Mitigation |
|-----------|--------|------|-----------|
| Truck Gateway | Spoofing | High | Firmware signature, JWT |
| Telemetry API | Tampering | High | HTTPS + Pydantic |
| Auth Server | Spoofing | Critical | RULE-006, rate limiting |
| IOC Enrichment | Info Disclosure | Medium | Secrets Manager |
| API Gateway | DoS | High | Rate limiting |
| Docker | Elevation | Critical | Non-root user |

## Risk Summary
- Critical: 3
- High: 5
- Medium: 2
- Low: 0
