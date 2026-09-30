# Baseline (v1.0.0) — Before CR-001

- **Commit hash**: `b7aeec951a59e82963f3e874a5764e39e7f6bf1e` (`b7aeec9`)
- **Branch**: `main`
- **Tests**: `8` passing, **Coverage**: `96%` (`794` statements, `29` missed)
- **Bandit**: `0` HIGH, `0` MEDIUM, `0` LOW (`1459` lines of code scanned)
- **Code smells (SonarQube)**: `0` (Quality Gate: `PASSED`)

## Modules (`22` modules excluding `__init__.py`)
1. `backend/app/celery_app.py`
2. `backend/app/config.py`
3. `backend/app/database.py`
4. `backend/app/digital_twin/event_trigger.py`
5. `backend/app/digital_twin/sync_engine.py`
6. `backend/app/digital_twin/twin_manager.py`
7. `backend/app/main.py`
8. `backend/app/models.py`
9. `backend/app/optimization/scenarios.py`
10. `backend/app/optimization/solver.py`
11. `backend/app/optimization/storage_interface.py`
12. `backend/app/routers/audit.py`
13. `backend/app/routers/auth.py`
14. `backend/app/routers/optimization.py`
15. `backend/app/routers/simulation.py`
16. `backend/app/routers/twin.py`
17. `backend/app/schemas.py`
18. `backend/app/security.py`
19. `backend/app/services/audit_service.py`
20. `backend/app/services/db_service.py`
21. `backend/app/services/notification_service.py`
22. `backend/app/simulation/runner.py`

## Raw Baseline Pytest Coverage Output
```text
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
app\__init__.py                             1      0   100%
app\celery_app.py                          17     17     0%   2-46
app\config.py                              35      1    97%   25
app\database.py                            17      5    71%   15, 32-36
app\digital_twin\__init__.py                0      0   100%
app\digital_twin\event_trigger.py          25      1    96%   26
app\digital_twin\sync_engine.py            26      0   100%
app\digital_twin\twin_manager.py           23      0   100%
app\main.py                                36      0   100%
app\models.py                              76      0   100%
app\optimization\__init__.py                0      0   100%
app\optimization\scenarios.py               4      0   100%
app\optimization\solver.py                 32      0   100%
app\optimization\storage_interface.py      53      0   100%
app\routers\__init__.py                     0      0   100%
app\routers\audit.py                       23      0   100%
app\routers\auth.py                        33      0   100%
app\routers\optimization.py                21      0   100%
app\routers\simulation.py                  18      0   100%
app\routers\twin.py                        26      0   100%
app\schemas.py                             97      0   100%
app\security.py                            76      2    97%   121-122
app\services\__init__.py                    0      0   100%
app\services\audit_service.py              52      1    98%   103
app\services\db_service.py                 58      2    97%   90-91
app\services\notification_service.py       19      0   100%
app\simulation\__init__.py                  0      0   100%
app\simulation\runner.py                   26      0   100%
---------------------------------------------------------------------
TOTAL                                     794     29    96%
======================= 8 passed, 2 warnings in 14.03s ========================
```
