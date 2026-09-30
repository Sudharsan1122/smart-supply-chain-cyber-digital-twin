# Change Request CR-001 — Partner Data Sharing

## Client Request (verbatim)
> "External suppliers must be able to log in and view ANONYMIZED demand 
> forecasts for their region, and CONFIRM weekly capacity commitments. 
> They must NOT see any other supplier's data or internal optimization 
> outputs. All commitment submissions must be cryptographically signed 
> and auditable. All data sharing must comply with our security policy."

## Impact Analysis

### New Artifacts Required
| Type | Name | Purpose |
|---|---|---|
| Model | `PartnerOrganization` | Supplier company entity; `org_id` scoping |
| Model | `PartnerCommitment` | Signed weekly capacity commitment |
| Role | `PARTNER` | RBAC role with org-scoped access |
| Router | `/api/partner/*` | Partner-scoped endpoints (`backend/app/routers/partner.py`) |
| Service | `PartnerService` | Anonymization + commitment logic (`backend/app/services/partner_service.py`) |
| Dependency | `get_partner_context` | Enforces `org_id` scoping (`backend/app/security.py`) |
| Constant | `PartnerConstants` | Centralized string constants (`backend/app/constants.py`) |
| Exception | `PartnerError` hierarchy | Specific typed errors (`backend/app/exceptions.py`) |

### Existing Modules Affected
| Module | Change | Risk |
|---|---|---|
| `backend/app/security.py` | Add `PARTNER` role + `require_role()` helper + `get_partner_context` + `sign_payload` / `verify_signature` | Low |
| `backend/app/models.py` | Add 2 tables (`PartnerOrganization`, `PartnerCommitment`) + `CommitmentStatus` enum | Medium |
| `backend/app/schemas.py` | Add partner DTOs (`PartnerForecastResponse`, `CommitmentCreate`, `CommitmentResponse`) | Low |
| `backend/app/main.py` | Register partner router under `/api/partner` | Low |
| `backend/app/services/audit_service.py` | Add 3 new event types (`PARTNER_FORECAST_VIEWED`, `PARTNER_COMMITMENT_CREATED`, `PARTNER_ACCESS_DENIED`) | Low |

### Threat Model Delta (STRIDE)
| Threat | STRIDE | Mitigation |
|---|---|---|
| Partner A reads Partner B data | Information Disclosure | Row-level filter by `org_id` on every query |
| Partner submits false commitment | Spoofing | HMAC-SHA256 signature + unique nonce |
| Forecast re-identification | Information Disclosure | $k$-anonymity ($k \ge 5$) aggregation |
| Partner escalates to PLANNER | Elevation of Privilege | Server-side role check via `require_role()` |
| Commitment replay | Tampering | Nonce + timestamp, reject duplicates with `409` |
| Forecast token leaks | Information Disclosure | Short TTL (24h), encrypted at rest |
| Audit log tampering | Repudiation | Append-only audit table with hash chain |

### Data Flow (new)
```text
    [Partner UI] --JWT--> [API Gateway] --role check--> [Partner Router]
                                                              |
                                                              v
                                                    [PartnerService] 
                                                              |
                                    +-------------------------+---------------------+
                                    v                         v                     v
                            [Anonymizer (k>=5)]      [Commitment Signer]     [Audit Service]
                                    |                         |                     |
                                    v                         v                     v
                            [Forecast Store]         [Commitment Table]      [Audit Log]
```

### Non-Functional Requirements (new)
- **NFR-09**: Partner endpoints must respond in $<500\text{ms}$ p95
- **NFR-10**: Commitment signature verified on every read
- **NFR-11**: Forecast data anonymized before serialization (never raw)
- **NFR-12**: Rate limit partner endpoints to 60 req/min per org

### Acceptance Criteria
- [x] `PARTNER` role can access `/api/partner/*` endpoints
- [x] Non-`PARTNER` roles receive `403`
- [x] Cross-org access returns `403` (tested)
- [x] $k < 5$ groups dropped / rejected from response
- [x] Commitment signature valid on create
- [x] Replayed nonce returns `409`
- [x] All actions emit audit events
- [x] Coverage on new code $\ge 90\%$

### CI/CD Impact
- No workflow changes needed
- New tests will execute in existing CI Pipeline (`ci.yml`)
- SonarQube quality gate must remain PASSED
- Trivy scan must remain 0 CRITICAL/HIGH
