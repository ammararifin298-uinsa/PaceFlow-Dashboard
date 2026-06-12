# 🏎️ PaceFlow — F1 Relational Analytics Dashboard

> Dashboard analitik Formula 1 berbasis arsitektur **Separation of Concerns (SoC)**  
> Stack: PostgreSQL → SQLAlchemy → Dash + Plotly  
> Bahasa: Python 100%

---

## Halaman Dashboard

| Halaman | Isi |
| --- | --- |
| 🏁 Beranda | Championship points progression dan klasemen konstruktor |
| 📊 Klasemen | Driver standings dan constructor standings |
| 📈 Analitik | Pit stop heatmap, speed trend, qualifying vs race |
| ⚔️ Head-to-Head | Radar chart perbandingan hingga 3 driver |
| ⚖️ Comparison | Perbandingan performa per season |
| 🗃️ Tabel Data | Raw data lengkap dari SQL View |
| ⚡ Benchmark | Perbandingan performa SQL View vs Pandas in-memory |
| ⚙️ Settings | Konfigurasi preferensi dashboard |
| ℹ️ Tentang | Informasi tim, arsitektur, teknologi, dan referensi |

---

## Prasyarat

Pastikan sudah terinstall di laptop:

- Python 3.10 atau lebih baru → https://www.python.org/downloads/
- Git → https://git-scm.com/downloads

**Opsional** (hanya jika ingin mode PostgreSQL penuh):
- PostgreSQL 14 atau lebih baru → https://www.postgresql.org/download/
- pgAdmin 4 → https://www.pgadmin.org/download/

> **Jika hanya ingin mencoba dashboard, tidak perlu install PostgreSQL** — gunakan `setup.bat` dan pilih Demo Mode.

---

## Cara Menjalankan (Step by Step)

### STEP 1 — Clone Repository

Buka terminal (Command Prompt / PowerShell / Terminal), lalu jalankan:

```
git clone https://github.com/ammararifin298-uinsa/PaceFlow-Dashboard.git
cd PaceFlow-Dashboard
```

### STEP 2 — Buat Virtual Environment

```
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac atau Linux
python3 -m venv .venv
source .venv/bin/activate
```

Jika berhasil, terminal akan menampilkan `(.venv)` di awal baris.

### STEP 3 — Install Dependencies

```
pip install -r requirements.txt
```

Tunggu sampai semua package selesai terinstall.

### STEP 4 — Buat Database di pgAdmin

1. Buka **pgAdmin**
2. Klik kanan **Databases** → **Create** → **Database**
3. Isi nama: `f1_analytics`
4. Klik **Save**

### STEP 5 — Konfigurasi Environment

```
cp .env.example .env
```

Buka file `.env` dengan text editor, isi password PostgreSQL anda:

```
PG_HOST=localhost
PG_PORT=5432
PG_DB=f1_analytics
PG_USER=postgres
PG_PASSWORD=isi_password_postgres_anda
F1_DEMO_MODE=false
F1_DATA_DIR=./Data
```

> **Catatan:** Password PostgreSQL adalah password yang anda buat saat install PostgreSQL pertama kali.

### STEP 6 — Siapkan Data CSV

Buat folder `Data` di dalam folder project, lalu masukkan file CSV berikut:

```
PaceFlow-Dashboard/
└── Data/
    ├── races.csv
    ├── race_results.csv
    ├── driver_standings.csv
    ├── constructor_standings.csv
    ├── pit_stops.csv
    ├── qualifying.csv
    ├── drivers.csv
    └── circuits.csv
```

> Dataset dapat diunduh di Kaggle: **Formula 1 World Championship (2024–2026)**

### STEP 7 — Jalankan ETL (Load CSV ke Database + Buat Views)

```
python etl_load.py
```

ETL secara otomatis:
1. Load semua CSV ke PostgreSQL
2. **Membuat semua SQL Views** (tidak perlu buka pgAdmin lagi)

Output yang diharapkan:

```
============================================================
F1 Analytics — ETL Pipeline
============================================================
Dropping existing views and tables...
  [OK] All dropped.
Loading CSV data...
  [OK] races                     →    70 rows loaded
  [OK] race_results              →  1024 rows loaded
  ...
Creating views...
  [OK] v_f1_analytics
  [OK] v_constructor_season
  [OK] v_kpi_summary
  [OK] v_driver_season_summary
  [OK] v_championship_progression
  [OK] v_constructor_progression
  [OK] v_dnf_causes
✅ ETL selesai. Jalankan: python app.py
```

### STEP 8 — Jalankan Dashboard

```
python app.py
```

Buka browser dan akses:

```
http://localhost:8050
```

Dashboard siap digunakan.

---

## 🚀 Cara Cepat — Satu Klik (Windows)

Cukup **double-click `setup.bat`** — script akan otomatis:
1. Cek Python tersedia
2. Buat `.env` dari template (default: Demo Mode)
3. Install semua dependencies
4. Jalankan dashboard

---

## Cara Cepat — Mode Demo (Tanpa PostgreSQL)

Jika tidak ingin setup PostgreSQL, gunakan mode demo:

**1. Salin template `.env`:**

```
copy .env.example .env
```

**2. Jalankan langsung:**

```
python app.py
```

Buka browser di `http://localhost:8050` — selesai, tidak perlu database.

> Mode demo menggunakan data real dari file `demo_cache.csv` yang sudah ada di repo.



## Troubleshooting

**Error: `password authentication failed for user "postgres"`**  
→ Password di file `.env` salah. Periksa kembali `PG_PASSWORD`.  
→ Test koneksi: jalankan `python -c "import psycopg2; psycopg2.connect(host='localhost', port=5432, dbname='f1_analytics', user='postgres', password='PASSWORD_ANDA'); print('OK')"`

**Error: `No module named 'dash_iconify'`**  
→ Jalankan: `pip install dash-iconify`

**Error: `No module named 'dash'`**  
→ Pastikan virtual environment aktif: `.venv\Scripts\activate` (Windows)  
→ Lalu: `pip install -r requirements.txt`

**Error: `database "f1_analytics" does not exist`**  
→ Buat database dulu di pgAdmin: klik kanan Databases → Create → Database → nama: `f1_analytics`

**Error: `cannot drop table races because other objects depend on it`**  
→ Jalankan di pgAdmin Query Tool:

```sql
DROP VIEW IF EXISTS v_kpi_summary CASCADE;
DROP VIEW IF EXISTS v_constructor_season CASCADE;
DROP VIEW IF EXISTS v_f1_analytics CASCADE;
```

→ Lalu jalankan ulang `python etl_load.py`

**Dashboard jalan tapi data kosong atau error di halaman**  
→ Pastikan ETL sudah berhasil (STEP 7)  
→ Pastikan SQL Views sudah dibuat (STEP 8)  
→ Atau gunakan mode demo: ubah `F1_DEMO_MODE=true` di `.env`

**Port 8050 sudah dipakai**  
→ Buka file `app.py`, cari baris paling bawah, ubah port:

```python
app.run(debug=False, host="0.0.0.0", port=8051)
```

---

## Struktur File

```
PaceFlow-Dashboard/
├── app.py                   # Entry point: layout utama, routing, global callbacks
├── layout/                  # Design system: komponen, tokens, sidebar, graph utils
├── pages/                   # 9 halaman: layout + callbacks per halaman
│   ├── home/                # Beranda — championship progression
│   ├── standings/           # Klasemen driver dan konstruktor
│   ├── analytics/           # Pit stop, speed trend, qualifying scatter
│   ├── h2h/                 # Head-to-Head radar chart (hingga 3 driver)
│   ├── comparison/          # Perbandingan performa antar season
│   ├── datatable/           # Tabel raw data dari SQL View
│   ├── benchmark/           # Benchmark SQL View vs Pandas
│   ├── settings/            # Konfigurasi preferensi
│   └── about/               # Informasi proyek
├── services/
│   └── data_service.py      # Service layer: LRU cache, schema enforcement
├── config.py                # Konfigurasi terpusat (env vars, team colors)
├── db.py                    # DAL: parameterized queries via SQLAlchemy
├── demo_data.py             # Data provider untuk mode demo (offline)
├── etl_load.py              # ETL pipeline: CSV → PostgreSQL + create views
├── schema_and_view.sql      # DDL: CREATE TABLE, INDEX, dan 6 SQL VIEW
├── demo_cache.csv           # Data cache untuk mode demo (disertakan di repo)
├── requirements.txt         # Daftar dependencies Python
├── setup.bat                # Script setup otomatis satu klik (Windows)
├── .env.example             # Template konfigurasi (salin ke .env)
├── .gitignore               # File yang diabaikan Git
└── Data/                    # Folder data CSV (tidak di-commit ke Git)
    ├── races.csv
    ├── race_results.csv
    ├── driver_standings.csv
    ├── constructor_standings.csv
    ├── pit_stops.csv
    ├── qualifying.csv
    ├── drivers.csv
    └── circuits.csv
```

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│  DATA LAYER — PostgreSQL                                    │
│                                                             │
│  races ──┐                                                  │
│  race_results ──┬──► LEFT JOIN ──► v_f1_analytics           │
│  driver_standings ──┘              v_constructor_season      │
│  pit_stops ──► agregasi            v_kpi_summary             │
│  qualifying ──► LEFT JOIN          v_driver_season_summary   │
│                                    v_championship_progression│
│  Index: season+round, driver_id, constructor_id             │
└────────────────────────┬────────────────────────────────────┘
                         │ SQLAlchemy (parameterized queries)
                         │ LRU Cache (13 fungsi, TTL = 600 detik)
┌────────────────────────▼────────────────────────────────────┐
│  SERVICE LAYER — data_service.py                            │
│  Single Source of Truth · enforce_schema() · invalidate()   │
│  Auto-fallback ke demo_data.py jika PostgreSQL offline      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  PRESENTATION LAYER — app.py (Dash + Plotly)                │
│  Sidebar navigasi · Filter season · 9 halaman               │
│  Export CSV · Benchmark chart · Help modal                  │
└─────────────────────────────────────────────────────────────┘
```

**Prinsip:** Separation of Concerns (SoC) sesuai ISO/IEC 25010  
Komputasi berat (JOIN, agregasi) dieksekusi di PostgreSQL.  
Dash hanya bertugas merender data yang sudah matang.  

---

## Referensi Akademis

- Hevner, A. R., March, S. T., Park, J., dan Ram, S. (2004). Design science in information systems research. *MIS Quarterly*, 28(1), 75–105.
- Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
- ISO/IEC 25010:2011. Systems and software Quality Requirements and Evaluation (SQuaRE).

---

*Dikembangkan sebagai bagian dari penelitian Tugas Akhir Sistem Informasi*  
*UIN Sunan Ampel Surabaya — 2026*
