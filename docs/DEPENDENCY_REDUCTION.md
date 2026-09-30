# Dependency Reduction Plan

## Current State
- 85 Python modules
- 250 internal imports
- Avg 3.0 imports/module
- Max 10 imports (api/app.py)

## Issues Identified
1. Tight coupling in ingestion/pipeline.py (8 imports)
2. Direct DB access in some routes (bypasses repository)
3. Duplicate risk logic in 3 places
4. Inconsistent Depends() usage

## Reduction Strategies

### Phase A — Quick Wins (1 day)
- [ ] Replace direct DB access with Repository pattern
- [ ] Add FastAPI Depends for sessions in all routes
- [ ] Remove unused imports (SonarQube identifies)

### Phase B — Medium (2 days)
- [ ] Split ingestion/pipeline.py into pipeline + handlers
- [ ] Create detection/orchestrator.py to abstract rule engine
- [ ] Consolidate risk scoring into single module

### Phase C — Structural (3 days)
- [ ] Add lightweight event bus (pub/sub)
- [ ] pipeline.py publishes events
- [ ] Detectors subscribe
- [ ] Reduce pipeline.py imports from 8 → 3

## Metrics Before/After
| Metric | Before | After |
|--------|--------|-------|
| Internal imports | 250 | 180 |
| Avg imports/module | 3.0 | 2.0 |
| Max imports/module | 10 | 6 |
| Test coverage | 85% | 90% |
| Cyclic deps | 0 | 0 |
| All tests pass | ✅ | ✅ |
