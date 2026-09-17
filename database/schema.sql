-- Phase 2+ -- Full schema (20 tables)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS assets (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id    VARCHAR(64)  NOT NULL UNIQUE,
    asset_type  VARCHAR(50)  NOT NULL,
    name        VARCHAR(128) NOT NULL,
    parent_id   BIGINT REFERENCES assets(id) ON DELETE SET NULL,
    metadata    JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);

CREATE TABLE IF NOT EXISTS telemetry (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id    BIGINT       NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    metric      VARCHAR(64)  NOT NULL,
    value       DOUBLE PRECISION,
    unit        VARCHAR(32),
    source      VARCHAR(64),
    payload     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    timestamp   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_telemetry_asset_time ON telemetry(asset_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS security_events (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id    BIGINT       NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    event_type  VARCHAR(64)  NOT NULL,
    severity    VARCHAR(16)  NOT NULL DEFAULT 'info',
    description TEXT,
    source      VARCHAR(64),
    payload     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    timestamp   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_events_asset ON security_events(asset_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS twin_states (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id    BIGINT       NOT NULL UNIQUE REFERENCES assets(id) ON DELETE CASCADE,
    state       VARCHAR(32)  NOT NULL DEFAULT 'unknown',
    health      VARCHAR(32)  NOT NULL DEFAULT 'unknown',
    position    JSONB        NOT NULL DEFAULT '{}'::jsonb,
    metrics     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    last_seen   TIMESTAMPTZ,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS state_transitions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id        BIGINT      NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    from_state      VARCHAR(32),
    to_state        VARCHAR(32) NOT NULL,
    reason          TEXT,
    transitioned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS detections (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id       BIGINT       NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    telemetry_id   BIGINT       REFERENCES telemetry(id) ON DELETE SET NULL,
    detection_type VARCHAR(16)  NOT NULL CHECK (detection_type IN ('rule','ml')),
    rule_id        VARCHAR(64),
    model_version  VARCHAR(64),
    confidence     DOUBLE PRECISION,
    severity       VARCHAR(16)  NOT NULL DEFAULT 'medium',
    description    TEXT,
    detected_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_detections_asset ON detections(asset_id, detected_at DESC);

CREATE TABLE IF NOT EXISTS risk_scores (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id      BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    score         DOUBLE PRECISION NOT NULL CHECK (score >= 0 AND score <= 100),
    factors       JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version VARCHAR(64),
    scored_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_risk_asset ON risk_scores(asset_id, scored_at DESC);

CREATE TABLE IF NOT EXISTS attack_scenarios (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scenario_id        VARCHAR(64)  NOT NULL UNIQUE,
    name               VARCHAR(128) NOT NULL,
    description        TEXT,
    target_asset_types JSONB        NOT NULL DEFAULT '[]'::jsonb,
    params             JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS attack_stories (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    attack_id   VARCHAR(64)  NOT NULL UNIQUE DEFAULT gen_random_uuid()::text,
    scenario_id BIGINT REFERENCES attack_scenarios(id) ON DELETE SET NULL,
    title       VARCHAR(256) NOT NULL,
    narrative   TEXT,
    status      VARCHAR(32)  NOT NULL DEFAULT 'open',
    started_at  TIMESTAMPTZ,
    ended_at    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS iocs (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    value      VARCHAR(512) NOT NULL,
    ioc_type   VARCHAR(32)  NOT NULL,
    source     VARCHAR(64),
    confidence DOUBLE PRECISION,
    first_seen TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_seen  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (value, ioc_type)
);

CREATE TABLE IF NOT EXISTS ioc_enrichments (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ioc_id      BIGINT      NOT NULL REFERENCES iocs(id) ON DELETE CASCADE,
    provider    VARCHAR(64) NOT NULL,
    verdict     VARCHAR(32),
    raw         JSONB       NOT NULL DEFAULT '{}'::jsonb,
    enriched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_enr_ioc ON ioc_enrichments(ioc_id, enriched_at DESC);

CREATE TABLE IF NOT EXISTS blast_radius (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    attack_story_id   BIGINT REFERENCES attack_stories(id) ON DELETE CASCADE,
    source_asset_id   BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    impacted_asset_id BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    depth             INTEGER NOT NULL DEFAULT 1,
    impact_score      DOUBLE PRECISION,
    path              JSONB NOT NULL DEFAULT '[]'::jsonb,
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS triage (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    detection_id BIGINT      NOT NULL REFERENCES detections(id) ON DELETE CASCADE,
    verdict      VARCHAR(4)  NOT NULL CHECK (verdict IN ('TP','FP','FN','TN')),
    confidence   DOUBLE PRECISION,
    analyst      VARCHAR(64),
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS incidents (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incident_uid    VARCHAR(64)  NOT NULL UNIQUE,
    title           VARCHAR(256) NOT NULL,
    severity        VARCHAR(16)  NOT NULL DEFAULT 'medium',
    status          VARCHAR(32)  NOT NULL DEFAULT 'open',
    root_asset_id   BIGINT REFERENCES assets(id) ON DELETE SET NULL,
    rule_id         VARCHAR(64)  NOT NULL,
    confidence      DOUBLE PRECISION,
    description     TEXT,
    window_start    TIMESTAMPTZ  NOT NULL,
    window_end      TIMESTAMPTZ  NOT NULL,
    metadata        JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS incident_members (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    incident_id   BIGINT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    telemetry_id  BIGINT REFERENCES telemetry(id) ON DELETE CASCADE,
    event_id      BIGINT REFERENCES security_events(id) ON DELETE CASCADE,
    role          VARCHAR(32) NOT NULL DEFAULT 'evidence',
    added_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS twin_state_snapshots (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id          BIGINT       NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    snapshot_type     VARCHAR(8)   NOT NULL CHECK (snapshot_type IN ('full','delta')),
    state             VARCHAR(32),
    health            VARCHAR(32),
    position          JSONB        NOT NULL DEFAULT '{}'::jsonb,
    metrics_full      JSONB        NOT NULL DEFAULT '{}'::jsonb,
    metrics_patch     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    transition_reason TEXT,
    recorded_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transition_anomalies (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_id      BIGINT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    transition_id BIGINT REFERENCES state_transitions(id) ON DELETE SET NULL,
    machine       VARCHAR(32)  NOT NULL,
    from_state    VARCHAR(32),
    to_state      VARCHAR(32)  NOT NULL,
    reason        VARCHAR(256) NOT NULL,
    severity      VARCHAR(16)  NOT NULL DEFAULT 'medium',
    kind          VARCHAR(32)  NOT NULL DEFAULT 'invalid_transition',
    detected_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS attack_story_events (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    story_id      BIGINT      NOT NULL REFERENCES attack_stories(id) ON DELETE CASCADE,
    evidence_kind VARCHAR(32) NOT NULL,
    evidence_id   BIGINT,
    occurred_at   TIMESTAMPTZ NOT NULL,
    asset_id      BIGINT REFERENCES assets(id) ON DELETE SET NULL,
    severity      VARCHAR(16),
    title         VARCHAR(256) NOT NULL,
    details       JSONB       NOT NULL DEFAULT '{}'::jsonb,
    tactic        VARCHAR(64),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS attack_story_tactics (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    story_id       BIGINT      NOT NULL REFERENCES attack_stories(id) ON DELETE CASCADE,
    tactic         VARCHAR(64) NOT NULL,
    confidence     DOUBLE PRECISION,
    evidence_count INTEGER     NOT NULL DEFAULT 0,
    first_seen     TIMESTAMPTZ,
    last_seen      TIMESTAMPTZ,
    notes          TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (story_id, tactic)
);

CREATE TABLE IF NOT EXISTS ioc_observations (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ioc_id          BIGINT      NOT NULL REFERENCES iocs(id) ON DELETE CASCADE,
    asset_id        BIGINT      REFERENCES assets(id) ON DELETE SET NULL,
    attack_story_id BIGINT      REFERENCES attack_stories(id) ON DELETE SET NULL,
    evidence_kind   VARCHAR(32) NOT NULL,
    evidence_id     BIGINT,
    context         JSONB       NOT NULL DEFAULT '{}'::jsonb,
    first_seen      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen       TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurrences     INTEGER     NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_ioc_obs_ioc ON ioc_observations(ioc_id);
CREATE INDEX IF NOT EXISTS idx_ioc_obs_asset ON ioc_observations(asset_id);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_assets_updated_at ON assets;
CREATE TRIGGER trg_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
