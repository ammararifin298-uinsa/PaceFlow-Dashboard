-- =============================================================================
-- F1 ANALYTICS DASHBOARD — DATABASE LAYER
-- Project   : Formula 1 Live Tracker 2024-2026
-- Purpose   : DDL + CREATE VIEW untuk arsitektur pemisahan beban komputasi
-- Standard  : Separation of Concerns (SoC) — ISO/IEC 25010
-- Updated   : 2026 — tambah 3 tabel baru, 3 view baru, fix DNF, fix KPI
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

CREATE TABLE IF NOT EXISTS constructor_standings (
    season          INTEGER       NOT NULL,
    round           INTEGER       NOT NULL,
    position        INTEGER,
    points          NUMERIC(7,2),
    wins            INTEGER,
    constructor_id  VARCHAR(50)   NOT NULL,
    constructor     VARCHAR(80),
    PRIMARY KEY (season, round, constructor_id)
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

CREATE TABLE IF NOT EXISTS drivers (
    driver_id       VARCHAR(50)   NOT NULL,
    driver_name     VARCHAR(100),
    driver_code     VARCHAR(5),
    driver_number   INTEGER,
    date_of_birth   DATE,
    nationality     VARCHAR(60),
    url             TEXT,
    PRIMARY KEY (driver_id)
);

CREATE TABLE IF NOT EXISTS circuits (
    circuit_id      VARCHAR(50)   NOT NULL,
    circuit_name    VARCHAR(100),
    city            VARCHAR(80),
    country         VARCHAR(80),
    lat             NUMERIC(9,6),
    lng             NUMERIC(9,6),
    url             TEXT,
    PRIMARY KEY (circuit_id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 2: INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_rr_season_round      ON race_results(season, round);
CREATE INDEX IF NOT EXISTS idx_rr_driver_id         ON race_results(driver_id);
CREATE INDEX IF NOT EXISTS idx_rr_constructor_id    ON race_results(constructor_id);
CREATE INDEX IF NOT EXISTS idx_ds_season_round      ON driver_standings(season, round);
CREATE INDEX IF NOT EXISTS idx_cs_season_round      ON constructor_standings(season, round);
CREATE INDEX IF NOT EXISTS idx_ps_season_round      ON pit_stops(season, round);
CREATE INDEX IF NOT EXISTS idx_ps_driver_id         ON pit_stops(driver_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 3: PRIMARY ANALYTICS VIEW — v_f1_analytics
-- Fix: is_dnf, is_finished, season_cumulative_points, leader_constructor
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW v_f1_analytics AS
SELECT
    rr.season,
    rr.round,
    rr.race_name,
    rc.race_date,
    rc.country,
    rc.city,
    rc.circuit_name,
    rc.lat,
    rc.lng,
    rr.driver_id,
    rr.driver_code,
    rr.driver_name,
    rr.driver_nat,
    rr.driver_number,
    rr.constructor_id,
    rr.constructor,
    rr.position,
    rr.position_text,
    rr.points                                           AS race_points,
    rr.grid_pos,
    rr.laps,
    rr.status,
    rr.avg_speed_kph,
    rr.fastest_lap_time,
    rr.fastest_lap_rank,
    (rr.grid_pos - rr.position)                         AS positions_gained,

    -- Flag Podium & Kemenangan
    CASE WHEN rr.position = 1  THEN TRUE ELSE FALSE END AS is_win,
    CASE WHEN rr.position <= 3 THEN TRUE ELSE FALSE END AS is_podium,

    -- FIX: is_finished — +1 Lap dst bukan DNF
    CASE WHEN rr.status IN (
        'Finished','+1 Lap','+2 Laps','+3 Laps','+4 Laps',
        '+5 Laps','+6 Laps','+7 Laps','+8 Laps','+9 Laps','+10 Laps'
    ) THEN TRUE ELSE FALSE END                          AS is_finished,

    -- FIX: is_dnf — hanya status yang benar-benar DNF
    CASE WHEN rr.status NOT IN (
        'Finished','+1 Lap','+2 Laps','+3 Laps','+4 Laps',
        '+5 Laps','+6 Laps','+7 Laps','+8 Laps','+9 Laps','+10 Laps'
    ) THEN TRUE ELSE FALSE END                          AS is_dnf,

    -- Standings dari driver_standings
    ds.points                                           AS cumulative_points,
    ds.position                                         AS championship_pos,
    ds.wins                                             AS cumulative_wins,

    -- FIX: season_cumulative_points — tidak bocor lintas season
    SUM(rr.points) OVER (
        PARTITION BY rr.driver_id, rr.season
        ORDER BY rr.round
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                                   AS season_cumulative_points,

    -- Pit stop agregasi
    ps_agg.total_stops,
    ps_agg.avg_duration_s                               AS avg_pit_duration_s,
    ps_agg.min_duration_s                               AS best_pit_duration_s,

    -- Qualifying
    q.position                                          AS qualifying_pos,
    q.q3                                                AS best_quali_time

FROM race_results rr
INNER JOIN races rc
    ON rr.season = rc.season AND rr.round = rc.round
INNER JOIN driver_standings ds
    ON rr.season = ds.season AND rr.round = ds.round AND rr.driver_id = ds.driver_id
LEFT JOIN (
    SELECT season, round, driver_id,
        COUNT(stop)     AS total_stops,
        AVG(duration_s) AS avg_duration_s,
        MIN(duration_s) AS min_duration_s
    FROM pit_stops
    WHERE is_red_flag_hold = FALSE
    GROUP BY season, round, driver_id
) ps_agg
    ON rr.season = ps_agg.season AND rr.round = ps_agg.round AND rr.driver_id = ps_agg.driver_id
LEFT JOIN qualifying q
    ON rr.season = q.season AND rr.round = q.round AND rr.driver_id = q.driver_id;

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 4: SUPPLEMENTARY VIEWS
-- ─────────────────────────────────────────────────────────────────────────────

-- View 1: Constructor per season
CREATE OR REPLACE VIEW v_constructor_season AS
SELECT
    season,
    constructor,
    constructor_id,
    COUNT(*) FILTER (WHERE is_win)              AS total_wins,
    COUNT(*) FILTER (WHERE is_podium)           AS total_podiums,
    SUM(race_points)                            AS total_points,
    ROUND(AVG(avg_speed_kph)::NUMERIC, 3)       AS avg_speed_kph,
    ROUND(AVG(avg_pit_duration_s)::NUMERIC, 3)  AS avg_pit_s
FROM v_f1_analytics
GROUP BY season, constructor, constructor_id
ORDER BY season, total_points DESC;

-- View 2: KPI summary — FIX leader_constructor, is_dnf, latest_standing
CREATE OR REPLACE VIEW v_kpi_summary AS
WITH latest_standing AS (
    SELECT DISTINCT ON (season, driver_id)
        season, driver_id, driver_name, constructor, points
    FROM driver_standings
    ORDER BY season, driver_id, round DESC
),
ranked AS (
    SELECT season, driver_id, driver_name, constructor, points,
        ROW_NUMBER() OVER (PARTITION BY season ORDER BY points DESC) AS rn
    FROM latest_standing
)
SELECT
    v.season,
    COUNT(DISTINCT v.race_name)                         AS total_races,
    COUNT(DISTINCT v.driver_id)                         AS total_drivers,
    COUNT(DISTINCT v.constructor_id)                    AS total_constructors,
    r.driver_name                                       AS points_leader,
    r.points                                            AS leader_points,
    r.constructor                                       AS leader_constructor,
    ROUND(AVG(v.avg_pit_duration_s)::NUMERIC, 2)        AS season_avg_pit_s,
    COUNT(*) FILTER (WHERE v.is_dnf = TRUE)             AS total_dnf,
    COUNT(*)                                            AS total_entries
FROM v_f1_analytics v
JOIN ranked r ON v.season = r.season AND r.rn = 1
GROUP BY v.season, r.driver_name, r.points, r.constructor;

-- ─────────────────────────────────────────────────────────────────────────────
-- SECTION 5: NEW VIEWS
-- ─────────────────────────────────────────────────────────────────────────────

-- View 3: Driver season summary — pure SQL agregasi, tidak perlu Pandas
CREATE OR REPLACE VIEW v_driver_season_summary AS
SELECT
    season,
    driver_id,
    driver_name,
    driver_nat,
    driver_code,
    constructor,
    constructor_id,
    MAX(championship_pos)                                           AS championship_pos,
    MAX(cumulative_points)                                          AS cumulative_points,
    MAX(cumulative_wins)                                            AS cumulative_wins,
    SUM(race_points)                                                AS total_points,
    COUNT(*)                                                        AS total_races,
    ROUND(AVG(race_points)::NUMERIC, 2)                             AS avg_points_per_race,
    COUNT(*) FILTER (WHERE is_win)                                  AS total_wins,
    COUNT(*) FILTER (WHERE is_podium)                               AS total_podiums,
    COUNT(*) FILTER (WHERE is_dnf)                                  AS total_dnf,
    COUNT(*) FILTER (WHERE qualifying_pos = 1)                      AS total_poles,
    COUNT(*) FILTER (WHERE fastest_lap_rank = 1)                    AS total_fl,
    -- Rates — tidak perlu hitung di Python lagi
    ROUND(COUNT(*) FILTER (WHERE is_win)::NUMERIC
          / NULLIF(COUNT(*), 0) * 100, 1)                           AS win_rate,
    ROUND(COUNT(*) FILTER (WHERE is_podium)::NUMERIC
          / NULLIF(COUNT(*), 0) * 100, 1)                           AS podium_rate,
    ROUND(COUNT(*) FILTER (WHERE is_dnf)::NUMERIC
          / NULLIF(COUNT(*), 0) * 100, 1)                           AS dnf_rate,
    ROUND(COUNT(*) FILTER (WHERE qualifying_pos = 1)::NUMERIC
          / NULLIF(COUNT(*), 0) * 100, 1)                           AS pole_rate,
    ROUND(COUNT(*) FILTER (WHERE fastest_lap_rank = 1)::NUMERIC
          / NULLIF(COUNT(*), 0) * 100, 1)                           AS fl_rate,
    -- Consistency Score — metrik unik PaceFlow (0-100)
    ROUND(
        (
            COALESCE(COUNT(*) FILTER (WHERE is_podium)::NUMERIC
                / NULLIF(COUNT(*), 0) * 40, 0) +
            COALESCE((1 - COUNT(*) FILTER (WHERE is_dnf)::NUMERIC
                / NULLIF(COUNT(*), 0)) * 30, 0) +
            COALESCE(AVG(race_points)::NUMERIC
                / NULLIF(MAX(AVG(race_points)) OVER (PARTITION BY season), 0) * 30, 0)
        )::NUMERIC, 1
    )                                                               AS consistency_score
FROM v_f1_analytics
GROUP BY season, driver_id, driver_name, driver_nat, driver_code,
         constructor, constructor_id
ORDER BY season, championship_pos;

-- View 4: Championship progression — per round per driver
CREATE OR REPLACE VIEW v_championship_progression AS
SELECT
    season,
    round,
    race_name,
    race_date,
    driver_id,
    driver_name,
    driver_code,
    constructor,
    race_points,
    season_cumulative_points,
    championship_pos,
    is_win,
    is_podium,
    is_dnf
FROM v_f1_analytics
ORDER BY season, driver_id, round;

-- View 5: Constructor championship progression — dari constructor_standings
CREATE OR REPLACE VIEW v_constructor_progression AS
SELECT
    cs.season,
    cs.round,
    cs.constructor_id,
    cs.constructor,
    cs.points                                           AS cumulative_points,
    cs.position                                         AS championship_pos,
    cs.wins                                             AS cumulative_wins,
    rc.race_name,
    rc.race_date
FROM constructor_standings cs
LEFT JOIN races rc
    ON cs.season = rc.season AND cs.round = rc.round
ORDER BY cs.season, cs.constructor_id, cs.round;

-- View 6: DNF causes breakdown — untuk donut chart di Analitik
CREATE OR REPLACE VIEW v_dnf_causes AS
SELECT
    season,
    status                                              AS dnf_cause,
    COUNT(*)                                            AS total,
    ROUND(COUNT(*)::NUMERIC
          / SUM(COUNT(*)) OVER (PARTITION BY season) * 100, 1) AS percentage
FROM race_results
WHERE status NOT IN (
    'Finished','+1 Lap','+2 Laps','+3 Laps','+4 Laps',
    '+5 Laps','+6 Laps','+7 Laps','+8 Laps','+9 Laps','+10 Laps'
)
GROUP BY season, status
ORDER BY season, total DESC;