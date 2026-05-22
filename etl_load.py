"""
=============================================================================
F1 Analytics Dashboard — ETL Script (CSV → PostgreSQL)
Project   : Formula 1 Live Tracker 2024-2026
=============================================================================
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_URL

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────────────────────────────────────
ENGINE_URL = DB_URL  # dibaca dari config.py → .env
DATA_DIR   = "./Data"

# ─────────────────────────────────────────────────────────────────────────────
# TRANSFORM HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def load_races(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"date": "race_date", "time": "race_time"})
    df["race_date"] = pd.to_datetime(df["race_date"], errors="coerce")
    return df[["season","round","race_name","race_date","race_time",
               "circuit_id","circuit_name","city","country","lat","lng","url"]]

def load_race_results(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"date": "race_date"})
    df["race_date"]        = pd.to_datetime(df["race_date"], errors="coerce")
    df["fastest_lap_rank"] = pd.to_numeric(df["fastest_lap_rank"], errors="coerce").astype("Int64")
    df["position"]         = pd.to_numeric(df["position"], errors="coerce").astype("Int64")
    df["grid_pos"]         = pd.to_numeric(df["grid_pos"], errors="coerce").astype("Int64")
    return df[[
        "season","round","race_name","race_date","position","position_text",
        "points","driver_id","driver_code","driver_number","driver_name",
        "driver_nat","constructor_id","constructor","grid_pos","laps",
        "status","time_finished","fastest_lap_time","fastest_lap_rank","avg_speed_kph"
    ]]

def load_driver_standings(path):
    df = pd.read_csv(path)
    df["position"] = pd.to_numeric(df["position"], errors="coerce")
    return df[[
        "season","round","position","points","wins",
        "driver_id","driver_name","driver_nat","constructor_id","constructor"
    ]]

def load_pit_stops(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"time": "stop_time"})
    return df[[
        "season","round","race_name","driver_id","stop",
        "lap","stop_time","duration_s","is_red_flag_hold"
    ]]

def load_qualifying(path):
    df = pd.read_csv(path)
    return df[[
        "season","round","race_name","position","driver_id",
        "driver_name","constructor_id","constructor","q1","q2","q3"
    ]]

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ETL
# ─────────────────────────────────────────────────────────────────────────────

TABLE_MAP = {
    "races":            (load_races,            "races.csv"),
    "race_results":     (load_race_results,     "race_results.csv"),
    "driver_standings": (load_driver_standings, "driver_standings.csv"),
    "pit_stops":        (load_pit_stops,        "pit_stops.csv"),
    "qualifying":       (load_qualifying,       "qualifying.csv"),
}

def run_etl():
    print("=" * 60)
    print("F1 Analytics — ETL Pipeline")
    print("=" * 60)

    engine = create_engine(ENGINE_URL, echo=False)

    with engine.begin() as conn:
        # Step 1: Drop views dan tables dengan CASCADE
        print("Dropping existing views and tables...")
        conn.execute(text("DROP VIEW IF EXISTS v_kpi_summary CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS v_constructor_season CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS v_f1_analytics CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS qualifying CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pit_stops CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS driver_standings CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS race_results CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS races CASCADE"))
        print("  [OK] All dropped.")

    # Step 2: Load CSV ke tabel
    print("\nLoading CSV data...")
    for table_name, (loader_fn, csv_file) in TABLE_MAP.items():
        csv_path = os.path.join(DATA_DIR, csv_file)
        if not os.path.exists(csv_path):
            print(f"  [SKIP] {csv_file} not found at {csv_path}")
            continue
        df = loader_fn(csv_path)
        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=500,
        )
        print(f"  [OK] {table_name:25s} → {len(df):>5} rows loaded")

    # Step 3: Buat Views
    print("\nCreating views...")
    sql_file = os.path.join(os.path.dirname(__file__), "schema_and_view.sql")
    with open(sql_file, "r") as f:
        ddl_sql = f.read()

    with engine.begin() as conn:
        statements = [s.strip() for s in ddl_sql.split(";") if s.strip()]
        for stmt in statements:
            # Hanya jalankan CREATE VIEW dan CREATE INDEX
            if stmt.upper().startswith(("CREATE OR REPLACE VIEW", "CREATE INDEX")):
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"  [WARN] {e!s:.80}")

    print("  [OK] Views created.")
    print("\n✅ ETL selesai. Jalankan: python app.py")

if __name__ == "__main__":
    run_etl()