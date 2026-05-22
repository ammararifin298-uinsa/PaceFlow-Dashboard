import sys
sys.path.insert(0, '.')
from sqlalchemy import create_engine, text
from config import DB_URL

engine = create_engine(DB_URL)

print('=== VALIDASI DATA AKTUAL ===')
queries = {
    'race_results rows':         'SELECT COUNT(*) FROM race_results',
    'races rows':                'SELECT COUNT(*) FROM races',
    'pit_stops rows':            'SELECT COUNT(*) FROM pit_stops',
    'qualifying rows':           'SELECT COUNT(*) FROM qualifying',
    'driver_standings rows':     'SELECT COUNT(*) FROM driver_standings',
    'unique driver_id':          'SELECT COUNT(DISTINCT driver_id) FROM race_results',
    'unique constructor_id':     'SELECT COUNT(DISTINCT constructor_id) FROM race_results',
    'unique seasons':            'SELECT COUNT(DISTINCT season) FROM races',
    'v_f1_analytics rows':       'SELECT COUNT(*) FROM v_f1_analytics',
    'pit_stops (no red flag)':   "SELECT COUNT(*) FROM pit_stops WHERE is_red_flag_hold = FALSE",
}

with engine.connect() as conn:
    for label, q in queries.items():
        r = conn.execute(text(q)).fetchone()[0]
        print(f'  {label:<35} = {r:,}')

    print()
    print('=== PER SEASON ===')
    rows = conn.execute(text(
        'SELECT season, COUNT(DISTINCT round) as races, COUNT(DISTINCT driver_id) as drivers,'
        'COUNT(DISTINCT constructor_id) as constructors, COUNT(*) as entries '
        'FROM race_results GROUP BY season ORDER BY season'
    )).fetchall()
    for row in rows:
        print(f'  Season {row[0]}: {row[1]} races, {row[2]} drivers, {row[3]} constructors, {row[4]} entries')

    print()
    print('=== avg_speed_kph PER SEASON ===')
    rows = conn.execute(text(
        'SELECT season, COUNT(*) as total, COUNT(avg_speed_kph) as has_speed '
        'FROM race_results GROUP BY season ORDER BY season'
    )).fetchall()
    for row in rows:
        pct = row[2]/row[1]*100 if row[1] > 0 else 0
        print(f'  Season {row[0]}: total={row[1]}, has_speed={row[2]} ({pct:.0f}%)')

    print()
    print('=== SQL VIEWS ===')
    rows = conn.execute(text(
        "SELECT table_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name"
    )).fetchall()
    for row in rows:
        print(f'  View: {row[0]}')

    print()
    print('=== SAMPLE avg_speed_kph 2024 ===')
    rows = conn.execute(text(
        'SELECT round, driver_name, avg_speed_kph FROM race_results '
        'WHERE season=2024 AND avg_speed_kph IS NOT NULL LIMIT 10'
    )).fetchall()
    if rows:
        for row in rows:
            print(f'  Round {row[0]} - {row[1]}: {row[2]} km/h')
    else:
        print('  TIDAK ADA DATA avg_speed_kph untuk season 2024!')
