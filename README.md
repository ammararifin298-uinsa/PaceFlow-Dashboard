# 🏎️ PaceFlow — F1 Relational Analytics Dashboard

> Dashboard analitik Formula 1 berbasis arsitektur **Separation of Concerns (SoC)**  
> Stack: PostgreSQL → SQLAlchemy → Dash + Plotly  
> Bahasa: Python 100%

---

## Halaman Dashboard

| Halaman | Isi |
|---|---|
| 🏁 Beranda | Championship points progression dan klasemen konstruktor |
| 📊 Klasemen | Driver standings dan constructor standings |
| 📈 Analitik | Pit stop heatmap, speed trend, qualifying vs race |
| ⚔️ Head-to-Head | Radar chart perbandingan hingga 3 driver |
| 🗃️ Tabel Data | Raw data lengkap dari SQL View |
| ⚡ Benchmark | Perbandingan performa SQL View vs Pandas in-memory |
| 📋 Evaluasi SUS | Form kuesioner System Usability Scale |

---

## Prasyarat

Pastikan sudah terinstall di laptop:

- Python 3.10 atau lebih baru → https://www.python.org/downloads/
- PostgreSQL 14 atau lebih baru → https://www.postgresql.org/download/
- pgAdmin 4 → https://www.pgadmin.org/download/
- Git → https://git-scm.com/downloads

---

## Cara Menjalankan (Step by Step)

### STEP 1 — Clone Repository

Buka terminal (Command Prompt / PowerShell / Terminal), lalu jalankan:

```bash
git clone https://github.com/ammararifin298-uinsa/PaceFlow-Dashboard.git
cd PaceFlow-Dashboard
```

### STEP 2 — Buat Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac atau Linux
python3 -m venv .venv
source .venv/bin/activate
```

Jika berhasil, terminal akan menampilkan `(.venv)` di awal baris.

### STEP 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Tunggu sampai semua package selesai terinstall.

### STEP 4 — Buat Database di pgAdmin

1. Buka **pgAdmin**
2. Klik kanan **Databases** → **Create** → **Database**
3. Isi nama: `f1_analytics`
4. Klik **Save**

### STEP 5 — Konfigurasi Environment

```bash
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

Buat folder `Data` di dalam folder project, lalu masukkan 5 file CSV berikut:

```
PaceFlow-Dashboard/
└── Data/
    ├── races.csv
    ├── race_results.csv
    ├── driver_standings.csv
    ├── pit_stops.csv
    └── qualifying.csv
```

> Dataset dapat diunduh di Kaggle: **Formula 1 Live Tracker 2024-2026**  
> Link: https://www.kaggle.com/datasets

### STEP 7 — Jalankan ETL (Load CSV ke Database)

```bash
python etl_load.py
```

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
  [OK] driver_standings          →  1083 rows loaded
  [OK] pit_stops                 →  1726 rows loaded
  [OK] qualifying                →  1021 rows loaded
Creating views...
  [OK] Views created.
✅ ETL selesai. Jalankan: python app.py
```

### STEP 8 — Buat SQL Views di pgAdmin

1. Buka **pgAdmin**
2. Klik database `f1_analytics`
3. Klik **Tools** → **Query Tool**
4. Buka file `schema_and_view.sql` dari folder project
5. Klik tombol **Execute / Run (F5)**
6. Pastikan muncul pesan `CREATE VIEW` tanpa error

### STEP 9 — Jalankan Dashboard

```bash
python app.py
```

Buka browser dan akses:

```
http://localhost:8050
```

Dashboard siap digunakan.

---

## Cara Cepat — Mode Demo (Tanpa PostgreSQL)

Jika tidak ingin setup PostgreSQL, gunakan mode demo yang menggunakan data yang sudah di-cache:

**1. Buka file `.env`**, ubah baris ini:

```
F1_DEMO_MODE=true
```

**2. Jalankan langsung:**

```bash
python app.py
```

Buka browser di `http://localhost:8050` — selesai, tidak perlu database.

> Mode demo menggunakan data real dari file `demo_cache.csv` yang sudah ada di repo.

---

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
├── app.py                   # Presentation layer (Dash + Plotly)
├── config.py                # Konfigurasi terpusat dan konstanta
├── db.py                    # Database access layer (Repository Pattern)
├── demo_data.py             # Data provider untuk mode demo
├── etl_load.py              # ETL pipeline: CSV ke PostgreSQL
├── benchmark.py             # Modul benchmark performa
├── sus_tool.py              # System Usability Scale tool
├── schema_and_view.sql      # DDL: CREATE TABLE, INDEX, dan VIEW
├── demo_cache.csv           # Data cache untuk mode demo
├── benchmark_results.json   # Hasil benchmark (auto-generated)
├── benchmark_summary.csv    # Ringkasan benchmark untuk paper
├── requirements.txt         # Daftar dependencies Python
├── .env.example             # Contoh konfigurasi (salin ke .env)
├── .gitignore               # File yang diabaikan Git
└── Data/                    # Folder data CSV (tidak di-commit ke Git)
    ├── races.csv
    ├── race_results.csv
    ├── driver_standings.csv
    ├── pit_stops.csv
    └── qualifying.csv
```

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│  DATA LAYER — PostgreSQL                                    │
│                                                             │
│  races ──┐                                                  │
│  race_results ──┬──► INNER JOIN ──► v_f1_analytics         │
│  driver_standings ──┘               v_constructor_season    │
│  pit_stops ──► agregasi             v_kpi_summary           │
│  qualifying ──► LEFT JOIN                                   │
│                                                             │
│  Index: season+round, driver_id, constructor_id             │
└────────────────────────┬────────────────────────────────────┘
                         │ SQLAlchemy (psycopg2 driver)
                         │ @st.cache_data TTL = 600 detik
┌────────────────────────▼────────────────────────────────────┐
│  MIDDLEWARE — db.py dan demo_data.py                        │
│  Repository Pattern: app.py tidak menulis SQL secara langsung│
│  Auto-fallback ke demo_data jika PostgreSQL tidak tersedia  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  PRESENTATION LAYER — app.py (Dash + Plotly)                │
│  Sidebar navigasi · Filter season · 7 halaman               │
│  Export CSV · SUS form · Benchmark chart                    │
└─────────────────────────────────────────────────────────────┘
```

**Prinsip:** Separation of Concerns (SoC) sesuai ISO/IEC 25010  
Komputasi berat (JOIN, agregasi) dieksekusi di PostgreSQL.  
Dash hanya bertugas merender data yang sudah matang.

---

## Referensi Akademis

- Brooke, J. (1996). SUS: A quick and dirty usability scale. *Usability Evaluation in Industry*, 189(194), 4–7.
- Bangor, A., Kortum, P. T., dan Miller, J. T. (2008). An empirical evaluation of the System Usability Scale. *International Journal of Human-Computer Interaction*, 24(6), 574–594.
- Hevner, A. R., March, S. T., Park, J., dan Ram, S. (2004). Design science in information systems research. *MIS Quarterly*, 28(1), 75–105.
- Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.
- ISO/IEC 25010:2011. Systems and software Quality Requirements and Evaluation (SQuaRE).

---

*Dikembangkan sebagai bagian dari penelitian Tugas Akhir Sistem Informasi*  
*UIN Sunan Ampel Surabaya — 2026*
