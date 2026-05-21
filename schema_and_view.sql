-- =============================================================================
-- F1 ANALYTICS DASHBOARD — DATABASE LAYER
-- Project   : Formula 1 Live Tracker 2024-2026
-- Purpose   : DDL + CREATE VIEW untuk arsitektur pemisahan beban komputasi
-- Standard  : Separation of Concerns (SoC) — ISO/IEC 25010
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 1: TABLE DEFINITIONS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS races (
    season          INTEGER       NOT NULL,
    round           INTEGER       NOT NULL,
    race_name       VARCHAR(100)  NOT NULL,
    race_date       DATE,
    race_time       TIME,
    circuit_id      VARCHAR(50),
    circuit_name    VARCHAR(100),
    city            VARCHAR(80),
    country         VARCHAR(80),
    lat             NUMERIC(9,6),
    lng             NUMERIC(9,6),
    url             TEXT,
    PRIMARY KEY (season, round)
);

CREATE TABLE IF NOT EXISTS race_results (
    season              INTEGER       NOT NULL,
    round               INTEGER       NOT NULL,
    race_name           VARCHAR(100),
    race_date           DATE,
    position            INTEGER,
    position_text       VARCHAR(10),
    points              NUMERIC(5,2),
    driver_id           VARCHAR(50)   NOT NULL,
    driver_code         VARCHAR(5),
    driver_number       INTEGER,
    driver_name         VARCHAR(100),
    driver_nat          VARCHAR(60),
    constructor_id      VARCHAR(50),
    constructor         VARCHAR(80),
    grid_pos            INTEGER,
    laps                INTEGER,
    status              VARCHAR(60),
    time_finished       VARCHAR(30),
    fastest_lap_time    VARCHAR(15),
    fastest_lap_rank    INTEGER,
    avg_speed_kph       NUMERIC(7,3),
    PRIMARY KEY (season, round, driver_id)
);

CREATE TABLE IF NOT EXISTS driver_standings (
    season          INTEGER       NOT NULL,
    round           INTEGER       NOT NULL,
    position        NUMERIC(5,1),
    points          NUMERIC(7,2),
    wins            INTEGER,
    driver_id       VARCHAR(50)   NOT NULL,
    driver_name     VARCHAR(100),
    driver_nat      VARCHAR(60),
    constructor_id  VARCHAR(50),
    constructor     VARCHAR(80),
    PRIMARY KEY (season, round, driver_id)
);

CREATE TABLE IF NOT EXISTS pit_stops (
    season              INTEGER       NOT NULL,
    round               INTEGER       NOT NULL,
    race_name           VARCHAR(100),
    driver_id           VARCHAR(50)   NOT NULL,
    stop                INTEGER       NOT NULL,
    lap                 INTEGER,
    stop_time           TIME,
    duration_s          NUMERIC(8,3),
    is_red_flag_hold    BOOLEAN       DEFAULT FALSE,
    PRIMARY KEY (season, round, driver_id, stop)
);

CREATE TABLE IF NOT EXISTS qualifying (
    season          INTEGER       NOT NULL,
    round           INTEGER       NOT NULL,
    race_name       VARCHAR(100),
    position        INTEGER,
    driver_id       VARCHAR(50)   NOT NULL,
    driver_name     VARCHAR(100),
    constructor_id  VARCHAR(50),
    constructor     VARCHAR(80),
    q1              VARCHAR(15),
    q2              VARCHAR(15),
    q3              VARCHAR(15),
    PRIMARY KEY (season, round, driver_id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 2: INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_rr_season_round      ON race_results(season, round);
CREATE INDEX IF NOT EXISTS idx_rr_driver_id         ON race_results(driver_id);
CREATE INDEX IF NOT EXISTS idx_rr_constructor_id    ON race_results(constructor_id);
CREATE INDEX IF NOT EXISTS idx_ds_season_round      ON driver_standings(season, round);
CREATE INDEX IF NOT EXISTS idx_ps_season_round      ON pit_stops(season, round);
CREATE INDEX IF NOT EXISTS idx_ps_driver_id         ON pit_stops(driver_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 3: PRIMARY ANALYTICS VIEW — v_f1_analytics
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW v_f1_analytics AS
SELECT
    -- Dimensi Waktu & Event
    rr.season,
    rr.round,
    rr.race_name,
    rc.race_date,
    rc.country,
    rc.city,
    rc.circuit_name,

    -- Dimensi Driver
    rr.driver_id,
    rr.driver_code,
    rr.driver_name,
    rr.driver_nat,
    rr.driver_number,

    -- Dimensi Constructor
    rr.constructor_id,
    rr.constructor,

    -- Metrik Hasil Race
    rr.position,
    rr.position_text,
    rr.points                                       AS race_points,
    rr.grid_pos,
    rr.laps,
    rr.status,
    rr.avg_speed_kph,
    rr.fastest_lap_time,
    rr.fastest_lap_rank,

    -- Grid-to-Finish Delta
    (rr.grid_pos - rr.position)                     AS positions_gained,

    -- Flag Podium & Kemenangan
    CASE WHEN rr.position = 1  THEN TRUE ELSE FALSE END AS is_win,
    CASE WHEN rr.position <= 3 THEN TRUE ELSE FALSE END AS is_podium,
    CASE WHEN rr.status = 'Finished' THEN TRUE ELSE FALSE END AS is_finished,

    -- Metrik Kumulatif Standings
    ds.points                                       AS cumulative_points,
    ds.position                                     AS championship_pos,
    ds.wins                                         AS cumulative_wins,

    -- Metrik Pit Stop (agregasi per race per driver)
    ps_agg.total_stops,
    ps_agg.avg_duration_s                           AS avg_pit_duration_s,
    ps_agg.min_duration_s                           AS best_pit_duration_s,

    -- Metrik Qualifying
    q.position                                      AS qualifying_pos,
    q.q3                                            AS best_quali_time

FROM race_results rr

INNER JOIN races rc
    ON rr.season = rc.season
    AND rr.round = rc.round

INNER JOIN driver_standings ds
    ON rr.season = ds.season
    AND rr.round = ds.round
    AND rr.driver_id = ds.driver_id

LEFT JOIN (
    SELECT
        season,
        round,
        driver_id,
        COUNT(stop)         AS total_stops,
        AVG(duration_s)     AS avg_duration_s,
        MIN(duration_s)     AS min_duration_s
    FROM pit_stops
    WHERE is_red_flag_hold = FALSE
    GROUP BY season, round, driver_id
) ps_agg
    ON rr.season = ps_agg.season
    AND rr.round = ps_agg.round
    AND rr.driver_id = ps_agg.driver_id

LEFT JOIN qualifying q
    ON rr.season = q.season
    AND rr.round = q.round
    AND rr.driver_id = q.driver_id;

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 4: SUPPLEMENTARY VIEWS
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW v_constructor_season AS
SELECT
    season,
    constructor,
    constructor_id,
    COUNT(*) FILTER (WHERE is_win)          AS total_wins,
    COUNT(*) FILTER (WHERE is_podium)       AS total_podiums,
    SUM(race_points)                        AS total_points,
    ROUND(AVG(avg_speed_kph)::NUMERIC, 3)   AS avg_speed_kph,
    ROUND(AVG(avg_pit_duration_s)::NUMERIC, 3) AS avg_pit_s
FROM v_f1_analytics
GROUP BY season, constructor, constructor_id
ORDER BY season, total_points DESC;

CREATE OR REPLACE VIEW v_kpi_summary AS
WITH ranked AS (
    SELECT
        season,
        driver_name,
        cumulative_points,
        ROW_NUMBER() OVER (PARTITION BY season ORDER BY cumulative_points DESC) AS rn
    FROM v_f1_analytics
)
SELECT
    v.season,
    COUNT(DISTINCT v.race_name)                         AS total_races,
    COUNT(DISTINCT v.driver_id)                         AS total_drivers,
    COUNT(DISTINCT v.constructor_id)                    AS total_constructors,
    r.driver_name                                       AS points_leader,
    r.cumulative_points                                 AS leader_points,
    ROUND(AVG(v.avg_pit_duration_s)::NUMERIC, 2)        AS season_avg_pit_s,
    COUNT(*) FILTER (WHERE v.is_finished = FALSE)       AS total_dnf
FROM v_f1_analytics v
JOIN ranked r ON v.season = r.season AND r.rn = 1
GROUP BY v.season, r.driver_name, r.cumulative_points;
