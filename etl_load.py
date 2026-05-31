"""
=============================================================================
F1 Analytics Dashboard — ETL Script (CSV → PostgreSQL)
Project   : Formula 1 Live Tracker 2024-2026
Update    : 2026 — tambah 3 tabel baru (constructor_standings, drivers, circuits)
Fix       : View creation pakai regex bukan split(";") agar CTE aman
=============================================================================
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os, sys, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DB_URL

ENGINE_URL = DB_URL
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

def load_constructor_standings(path):
    df = pd.read_csv(path)
    df["position"] = pd.to_numeric(df["position"], errors="coerce")
    df["points"]   = pd.to_numeric(df["points"], errors="coerce")
    df["wins"]     = pd.to_numeric(df["wins"], errors="coerce").fillna(0).astype(int)
    return df[[
        "season","round","position","points","wins",
        "constructor_id","constructor"
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

def load_drivers(path):
    df = pd.read_csv(path)
    col_map = {}
    if "driverRef"     in df.columns: col_map["driverRef"]     = "driver_id"
    if "forename"      in df.columns: col_map["forename"]      = "first_name"
    if "surname"       in df.columns: col_map["surname"]       = "last_name"
    if "code"          in df.columns: col_map["code"]          = "driver_code"
    if "number"        in df.columns: col_map["number"]        = "driver_number"
    if "permanent_num" in df.columns: col_map["permanent_num"] = "driver_number"
    if "dob"           in df.columns: col_map["dob"]           = "date_of_birth"
    if "given_name"    in df.columns: col_map["given_name"]    = "first_name"
    if "family_name"   in df.columns: col_map["family_name"]   = "last_name"
    if "full_name"     in df.columns: col_map["full_name"]     = "driver_name"
    df = df.rename(columns=col_map)
    if "date_of_birth" in df.columns:
        df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
    if "driver_name" not in df.columns and "first_name" in df.columns:
        df["driver_name"] = df["first_name"] + " " + df["last_name"]
    cols = ["driver_id","driver_name","driver_code","driver_number",
            "date_of_birth","nationality","url"]
    return df[[c for c in cols if c in df.columns]]

def load_circuits(path):
    df = pd.read_csv(path)
    col_map = {}
    if "circuitRef" in df.columns: col_map["circuitRef"] = "circuit_id"
    if "name"       in df.columns: col_map["name"]       = "circuit_name"
    if "location"   in df.columns: col_map["location"]   = "city"
    df = df.rename(columns=col_map)
    cols = ["circuit_id","circuit_name","city","country","lat","lng","url"]
    return df[[c for c in cols if c in df.columns]]

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ETL
# ─────────────────────────────────────────────────────────────────────────────

TABLE_MAP = {
    "races":                 (load_races,                "races.csv"),
    "race_results":          (load_race_results,         "race_results.csv"),
    "driver_standings":      (load_driver_standings,     "driver_standings.csv"),
    "constructor_standings": (load_constructor_standings,"constructor_standings.csv"),
    "pit_stops":             (load_pit_stops,            "pit_stops.csv"),
    "qualifying":            (load_qualifying,           "qualifying.csv"),
    "drivers":               (load_drivers,              "drivers.csv"),
    "circuits":              (load_circuits,             "circuits.csv"),
}

def create_views(engine, sql_file):
    """
    Buat views dari SQL file.
    Fix: pakai regex bukan split(";") agar CTE dengan ; di dalamnya aman.
    """
    with open(sql_file, "r") as f:
        ddl_sql = f.read()

    # Split berdasarkan keyword CREATE — bukan berdasarkan ;
    blocks = re.split(
        r'(?=\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:VIEW|INDEX)\b)',
        ddl_sql,
        flags=re.IGNORECASE
    )

    with engine.begin() as conn:
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            upper = block.upper()
            if not (upper.startswith("CREATE OR REPLACE VIEW") or
                    upper.startswith("CREATE INDEX")):
                continue
            # Hapus trailing semicolon
            stmt = block.rstrip().rstrip(";").strip()
            try:
                conn.execute(text(stmt))
                # Ambil nama view/index untuk log
                words = stmt.split()
                name  = words[4] if "OR" in words[1].upper() else words[2]
                print(f"  [OK] {name}")
            except Exception as e:
                print(f"  [WARN] {e!s:.120}")


def run_etl():
    print("=" * 60)
    print("F1 Analytics — ETL Pipeline")
    print("=" * 60)

    engine = create_engine(ENGINE_URL, echo=False)

    # Step 1: Drop views dan tables
    with engine.begin() as conn:
        print("Dropping existing views and tables...")
        for v in ["v_dnf_causes","v_constructor_progression",
                  "v_championship_progression","v_driver_season_summary",
                  "v_kpi_summary","v_constructor_season","v_f1_analytics"]:
            conn.execute(text(f"DROP VIEW IF EXISTS {v} CASCADE"))
        for t in ["qualifying","pit_stops","constructor_standings",
                  "driver_standings","race_results","races","drivers","circuits"]:
            conn.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE"))
        print("  [OK] All dropped.")

    # Step 2: Load CSV
    print("\nLoading CSV data...")
    for table_name, (loader_fn, csv_file) in TABLE_MAP.items():
        csv_path = os.path.join(DATA_DIR, csv_file)
        if not os.path.exists(csv_path):
            print(f"  [SKIP] {csv_file} not found")
            continue
        try:
            df = loader_fn(csv_path)
            df.to_sql(table_name, engine, if_exists="replace",
                      index=False, method="multi", chunksize=500)
            print(f"  [OK] {table_name:25s} → {len(df):>5} rows loaded")
        except Exception as e:
            print(f"  [ERROR] {table_name}: {e}")

    # Step 3: Create views
    print("\nCreating views...")
    sql_file = os.path.join(os.path.dirname(__file__), "schema_and_view.sql")
    create_views(engine, sql_file)
    print("\n✅ ETL selesai. Jalankan: python app.py")


if __name__ == "__main__":
    run_etl()