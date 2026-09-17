INSERT INTO assets (asset_id, asset_type, name, metadata) VALUES
('WH-001','WAREHOUSE','Chennai Central','{}'),
('WH-002','WAREHOUSE','Bengaluru Hub','{}'),
('WH-003','WAREHOUSE','Mumbai DC','{}'),
('WH-004','WAREHOUSE','Delhi NCR','{}'),
('TRUCK-001','TRUCK','Reefer 001','{}'),
('TRUCK-002','TRUCK','Reefer 002','{}'),
('TRUCK-003','TRUCK','Dry Van 003','{}'),
('TRUCK-004','TRUCK','Dry Van 004','{}'),
('TRUCK-005','TRUCK','Reefer 005','{}'),
('TRUCK-006','TRUCK','Dry Van 006','{}'),
('TRUCK-007','TRUCK','Dry Van 007','{}'),
('TRUCK-008','TRUCK','Reefer 008','{}'),
('API-GW-001','API_GATEWAY','North GW','{}'),
('API-GW-002','API_GATEWAY','West GW','{}'),
('SUP-001','SUPPLIER','Acme','{}'),
('SUP-002','SUPPLIER','NorthStar','{}'),
('SUP-003','SUPPLIER','Titan Steel','{}'),
('SUP-004','SUPPLIER','GreenLeaf','{}')
ON CONFLICT (asset_id) DO NOTHING;

INSERT INTO assets (asset_id, asset_type, name, parent_id, metadata)
SELECT v.a, v.t, v.n, a.id, '{}'::jsonb
FROM (VALUES
('TEMP-001','SENSOR','Temp WH-001 A','WH-001'),
('TEMP-002','SENSOR','Temp WH-001 B','WH-001'),
('HUM-001','SENSOR','Hum WH-001','WH-001'),
('HUM-002','SENSOR','Hum WH-003','WH-003'),
('DOOR-001','SENSOR','Door WH-001','WH-001'),
('DOOR-002','SENSOR','Door WH-004','WH-004'),
('VGW-101','VEHICLE_GATEWAY','GW 001','TRUCK-001'),
('VGW-102','VEHICLE_GATEWAY','GW 002','TRUCK-002'),
('VGW-103','VEHICLE_GATEWAY','GW 005','TRUCK-005'),
('VGW-104','VEHICLE_GATEWAY','GW 008','TRUCK-008'),
('AUTH-001','AUTH_SYSTEM','Identity','API-GW-001'),
('DB-001','DATABASE','PostgreSQL','API-GW-001'),
('APP-001','APPLICATION','Order Mgmt','API-GW-001'),
('APP-002','APPLICATION','Fleet Track','API-GW-002')
) AS v(a, t, n, p)
JOIN assets a ON a.asset_id = v.p
ON CONFLICT (asset_id) DO NOTHING;

INSERT INTO twin_states (asset_id, state, health, last_seen)
SELECT id, 'idle', 'unknown', now() FROM assets
ON CONFLICT (asset_id) DO NOTHING;

SELECT COUNT(*) AS assets_loaded FROM assets;
