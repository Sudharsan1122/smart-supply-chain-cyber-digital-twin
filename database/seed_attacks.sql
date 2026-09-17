INSERT INTO attack_scenarios (scenario_id, name, description, target_asset_types, params) VALUES
('SIM-01','Vehicle Gateway Compromise','Attacker compromises a vehicle gateway.','["VEHICLE_GATEWAY"]'::jsonb,'{"tick_seconds":2,"assets":["VGW-101"],"metrics":{"firmware":"v1.0.0","network_destinations":["1.1.1.1","2.2.2.2","3.3.3.3","4.4.4.4","5.5.5.5"],"unusual_api_calls":250,"status":"OFFLINE"}}'::jsonb),
('SIM-02','Warehouse IoT Compromise','Attacker pivots via warehouse IoT.','["WAREHOUSE"]'::jsonb,'{"tick_seconds":2,"assets":["WH-001"],"metrics":{"door_status":"OPEN","temperature":42.0,"occupancy":0}}'::jsonb),
('SIM-03','Credential Anomaly','Brute-force auth.','["AUTH_SYSTEM"]'::jsonb,'{"tick_seconds":1,"assets":["AUTH-001"],"metrics":{"failed_logins":12,"auth_events":30,"status":"OFFLINE"}}'::jsonb)
ON CONFLICT (scenario_id) DO NOTHING;
