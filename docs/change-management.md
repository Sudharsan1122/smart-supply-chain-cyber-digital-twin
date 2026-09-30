# Change Request CR-001 — Partner Data Sharing

## Client Request (verbatim)
> "External suppliers must be able to log in and view ANONYMIZED demand forecasts for their region, and CONFIRM weekly capacity commitments. They must NOT see any other supplier's data or internal optimization outputs. All commitment submissions must be cryptographically signed and auditable."

## Impact Analysis

### New Artifacts Required
| Type | Name | Purpose |
|---|---|---|
| Model | `PartnerOrganization` | Supplier entity, `org_id` scoping |
| Model | `PartnerCommitment` | Signed weekly capacity commitment |
| Role | `PARTNER` | RBAC role with org-scoped access |
| Router | `/api/partner/*` | Partner-scoped endpoints |
| Service | `PartnerService` | Anonymization + commitment logic |
| Dependency | `get_partner_context` | Enforces `org_id` scoping |

### Existing Modules Affected
| Module | Change | Risk |
|---|---|---|
| `app/security.py` | Add `PARTNER` role + `require_role()` helper + `get_partner_context` + `sign_payload` / `verify_signature` | Low |
| `app/models.py` | Add 2 tables (`PartnerOrganization`, `PartnerCommitment`) + FK relationship | Medium |
| `app/schemas.py` | Add partner DTOs (`PartnerForecastResponse`, `CommitmentCreate`, `CommitmentResponse`) | Low |
| `app/main.py` | Register partner router under `/api/partner` | Low |
| `app/services/audit_service.py` | Add 3 new event types (`PARTNER_FORECAST_VIEWED`, `PARTNER_COMMITMENT_CREATED`, `PARTNER_ACCESS_DENIED`) | Low |

### Threat Model Delta (STRIDE)
| Threat | STRIDE | Mitigation |
|---|---|---|
| Partner A reads Partner B data | Info Disclosure | Row-level filter by `org_id` in every query |
| Partner submits false commitment | Spoofing | HMAC-SHA256 signature + nonce |
| Forecast re-identification | Info Disclosure | $k$-anonymity with $k \ge 5$ |
| Partner escalates to PLANNER | Elevation | Server-side role check via `require_role()` |
| Commitment replay | Tampering | Nonce + timestamp, reject duplicates (`409 Conflict`) |
| Forecast token leaks | Info Disclosure | Short TTL (24h), encrypted at rest |

### CI/CD Impact
- No workflow changes needed (`.github/workflows/ci.yml` and `.github/workflows/deploy.yml` remain untouched)
- New tests will run in existing CI Pipeline
- SonarQube gate must remain PASSED
