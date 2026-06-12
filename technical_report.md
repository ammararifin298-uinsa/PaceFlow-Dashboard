# Laporan Teknis: PaceFlow — F1 Relational Analytics Dashboard

*Diperbarui: Juni 2026 — Mencerminkan kondisi aktual kode setelah audit menyeluruh*

---

## 1. Ringkasan Umum Proyek

- **Tujuan**: Membangun sistem dasbor analitik Formula 1 interaktif berbasis arsitektur *Separation of Concerns* (SoC) untuk memantau performa pembalap dan konstruktor.
- **Fungsi Utama**: Visualisasi *championship progression*, analisis kecepatan dan pit stop, *head-to-head* antar pembalap, komparasi antar-musim, inspeksi data tabel.
- **Stack Teknologi**:
  - **Database**: PostgreSQL 14+, SQLAlchemy 2.0+
  - **Middleware**: Python 3.10+, Pandas 2.2+, NumPy
  - **Frontend**: Dash 2+, Plotly 5+, Dash Bootstrap Components
- **Jenis Data**: Dataset historis F1 dari Ergast API (CSV): 8 tabel — races, race_results, driver_standings, constructor_standings, pit_stops, qualifying, drivers, circuits.
- **Alur Utama**: Komputasi berat (JOIN, agregasi) dieksekusi di PostgreSQL via *SQL Views*. Dash hanya merender data matang.
- **Resiliensi**: Terdapat *fallback mode* ke `demo_cache.csv` jika PostgreSQL tidak tersedia.

---

## 2. Arsitektur Sistem (4-Tier)

```
┌──────────────────────────────────────────────────────────┐
│  TIER 1: DATABASE LAYER — PostgreSQL                     │
│                                                          │
│  8 Tabel + 6 SQL Views:                                  │
│  v_f1_analytics          — master view (LEFT JOIN)       │
│  v_constructor_season    — agregasi konstruktor          │
│  v_kpi_summary           — indikator KPI per musim       │
│  v_driver_season_summary — statistik + consistency score │
│  v_championship_progression — titik kumulatif per round  │
│  v_constructor_progression  — progres konstruktor        │
│  v_dnf_causes            — breakdown penyebab DNF        │
└──────────────────────────┬───────────────────────────────┘
                           │ SQLAlchemy (parameterized queries)
                           │ Pool size: 3 koneksi
┌──────────────────────────▼───────────────────────────────┐
│  TIER 2: DATA ACCESS LAYER — db.py                       │
│                                                          │
│  - Semua query parameterized (:season) — aman dari SQL   │
│    injection                                             │
│  - Auto-fallback ke demo_data.py jika koneksi gagal      │
│  - Tidak ada @lru_cache di sini (hanya di service layer) │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  TIER 3: SERVICE LAYER — services/data_service.py        │
│                                                          │
│  - @lru_cache pada 13 fungsi (single source of truth)    │
│  - enforce_schema(): menjamin kolom wajib selalu ada     │
│  - invalidate_cache(): reset semua 13 cache sekaligus    │
│  - set_demo_mode(): thread-safe via threading.Lock()     │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│  TIER 4: PRESENTATION LAYER — app.py + pages/            │
│                                                          │
│  - 9 halaman modular (layout.py + callbacks.py)          │
│  - Global store: store-season, store-filter, store-page  │
│  - Export CSV, Help modal, Benchmark chart               │
└──────────────────────────────────────────────────────────┘
```

**Evaluasi**: Implementasi SoC sesuai ISO/IEC 25010. Tidak ada SQL raw di layer presentasi. Tidak ada logika bisnis di layer database.

---

## 3. Alur Data Lengkap

```
Raw CSV (Data/)
    → etl_load.py (ETL: konversi tipe, validasi, bulk insert)
    → PostgreSQL Tables (8 tabel)
    → PostgreSQL Views (6 views, komputasi dilakukan di DB engine)
    → db.py (parameterized query via SQLAlchemy)
    → data_service.py (LRU cache, schema enforcement)
    → pages/*/callbacks.py (reactive callbacks)
    → pages/*/layout.py (Plotly figures, Dash components)
    → Browser (render HTML/JS)
```

---

## 4. Detail Halaman Dashboard (9 Halaman)

| # | Halaman | Sumber Data | Visualisasi Utama |
|---|---------|-------------|-------------------|
| 1 | **Beranda** | v_championship_progression, v_kpi_summary | Line chart poin kumulatif, bump chart posisi, KPI cards |
| 2 | **Klasemen** | v_championship_progression, v_constructor_progression | Constructor progression dengan toggle Top 5/10/Semua |
| 3 | **Analitik** | v_f1_analytics | Boxplot pit stop, line speed trend, scatter qualifying-race, donut DNF |
| 4 | **Head-to-Head** | v_f1_analytics, v_driver_season_summary | Radar chart 6 metrik, bar chart, gauge consistency score |
| 5 | **Perbandingan** | v_f1_analytics, v_constructor_season | Multi-season comparison: points, wins, avg speed |
| 6 | **Tabel Data** | 5 tab: driver, constructor, calendar, qualifying, pit stops | Raw data table dengan filter interaktif |
| 7 | **Benchmark** | benchmark_results.json | Bar chart latensi SQL View vs Pandas |
| 8 | **Settings** | health_check(), get_etl_info() | Status koneksi DB, refresh cache |
| 9 | **Tentang** | Static | Informasi arsitektur dan referensi |

---

## 5. SQL View — Desain dan Keputusan Arsitektur

### v_f1_analytics (Master View)
- Menggabungkan 4 tabel: `race_results`, `races`, `driver_standings`, `pit_stops`, `qualifying`
- **Penting**: Menggunakan `LEFT JOIN` ke `driver_standings` (bukan INNER JOIN) untuk mencegah hilangnya data saat standings belum lengkap
- Menghitung: `is_win`, `is_podium`, `is_dnf`, `is_finished`, `season_cumulative_points` (via window function), agregasi pit stop

### v_driver_season_summary
- Menghitung `consistency_score` (formula: `podium_rate×0.4 + (100-dnf_rate)×0.3 + avg_pts_normalized×0.3`)
- Digunakan di halaman H2H (gauge chart) dan Klasemen

### v_dnf_causes
- Mengklasifikasi status sebagai DNF vs finished: status `Finished`, `Lapped`, `+1 Lap` dst dikecualikan dari DNF

---

## 6. Sistem Cache (LRU Cache)

| Fungsi | Parameter | Cache |
|--------|-----------|-------|
| get_analytics(season) | int | ✅ |
| get_kpi(season) | int | ✅ |
| get_constructor_season(season) | int | ✅ |
| get_seasons() | — | ✅ |
| get_calendar() | — | ✅ (all seasons) |
| get_driver_season_summary(season) | int | ✅ |
| get_championship_progression(season) | int | ✅ |
| get_constructor_progression(season) | int | ✅ |
| get_dnf_causes(season) | int | ✅ |
| get_drivers_info() | — | ✅ |
| get_circuits() | — | ✅ |
| get_qualifying(season) | int | ✅ |
| get_pit_stops(season) | int | ✅ |

`invalidate_cache()` me-reset semua 13 fungsi sekaligus. Dipanggil dari Settings page dan saat `set_demo_mode()`.

---

## 7. Sistem Callback Dash

### Pola Umum
- `prevent_initial_call=True` pada semua callback yang bergantung pada interaksi user
- `allow_duplicate=True` hanya pada callback yang memang perlu menulis ke store yang sama (datatable sync)
- Semua ID komponen unik secara global (konflik standings vs home sudah diselesaikan via prefix `btn-stnd-con-*`)

### Interaksi Legenda (Custom Legend Click)
Diimplementasikan via `restyleData` prop pada `dcc.Graph`:
- Klik 1x → isolasi/fokus pada 1 driver/tim
- Klik lagi → reset ke tampilan semua
- Dikelola oleh `layout/graph_utils.py:parse_restyle()` — satu implementasi dipakai di home dan analytics

### Global State
```
store-season  → season aktif (int)
store-seasons → list season untuk multi-compat
store-page    → halaman aktif (string)
store-filter  → {search, drv, con, status}
```

---

## 8. Benchmark — Metodologi Evaluasi

**Hipotesis**: Penggunaan SQL View (komputasi di database) lebih efisien dari komputasi Pandas in-memory untuk operasi agregasi skala besar.

**Skenario Pengujian**:
- **Kondisi A (Baseline)**: Load seluruh `race_results` → filter/agregasi di Pandas
- **Kondisi B (Proposed)**: Query langsung ke PostgreSQL View yang sudah teragregasi

**Metrik**: Execution time (ms) per operasi, rata-rata dari 5 run

**Output**: `benchmark_results.json` → divisualisasikan di halaman Benchmark

**Kelayakan Ilmiah**: Sesuai untuk metodologi *Design Science Research* (DSR) — membuktikan efektivitas artefak (SQL View + LRU Cache) secara empiris.

---

## 9. Demo Mode / Fallback

**Mekanisme**:
1. Saat startup, `config.py` baca `F1_DEMO_MODE` dari `.env`
2. Jika `true` atau PostgreSQL tidak terhubung → `_use_demo = True`
3. Semua pemanggilan di `data_service.py` dialihkan ke `demo_data.py`
4. `demo_data.py` membaca `demo_cache.csv` dan mensimulasikan output SQL View dengan Pandas filter

**Catatan Penting**: `demo_cache.csv` harus selaras dengan struktur kolom SQL View terbaru. Jika ada view baru ditambahkan, `demo_cache.csv` perlu di-regenerate.

---

## 10. Keputusan Desain yang Relevan untuk Paper

| Keputusan | Alasan | Trade-off |
|-----------|--------|-----------|
| SQL View untuk agregasi | Shift beban dari RAM Python ke DB engine | Terikat pada PostgreSQL, tidak bisa pakai SQLite |
| LRU Cache di service layer (bukan DAL) | DAL stateless, cache terpusat dan mudah di-invalidate | Cache tidak expire otomatis (TTL manual) |
| LEFT JOIN ke driver_standings | Mencegah hilangnya data race yang standings-nya belum diisi | Nilai standings bisa NULL (ditangani COALESCE) |
| Parameterized query (:season) | Keamanan dari SQL injection, standard SQLAlchemy | Sedikit lebih verbose |
| Demo mode dengan CSV fallback | Aplikasi tetap bisa demo tanpa PostgreSQL | Data statis, tidak real-time |
| Modular pages (layout + callbacks terpisah) | SoC — masing-masing halaman independent | Lebih banyak file, perlu koordinasi ID |

---

## 11. Klaim Ilmiah yang Valid

**AMAN ditulis di paper**:
- "Penggunaan SQL View secara signifikan mengurangi latensi komputasi dibandingkan agregasi Pandas in-memory"
- "Arsitektur 4-tier dengan LRU cache menghasilkan respons rata-rata < X ms untuk dataset 1000+ baris"
- "Implementasi SoC memungkinkan penambahan halaman baru tanpa modifikasi lapisan lain"
- "Consistency Score dirumuskan sebagai fungsi dari podium rate, DNF rate, dan normalized average points"

**TIDAK BOLEH ditulis**:
- Klaim kepuasan pengguna (tidak ada SUS/kuesioner)
- Klaim real-time (data bersumber dari CSV statis)
- Klaim skalabilitas tanpa load testing

---

## 12. Screenshot Wajib untuk Paper

1. **Arsitektur diagram** (dari README atau buat sendiri di draw.io)
2. **Halaman Beranda** — menunjukkan championship progression dengan toggle Top 5/10/Semua
3. **Halaman Analitik** — scatter posisi gained/lost, boxplot pit stop
4. **Halaman H2H** — radar chart 6-metrik, gauge consistency score
5. **Halaman Benchmark** — bar chart latensi sebagai bukti empiris evaluasi

---

## 13. Status Kesiapan: 100% Production-Ready

| Aspek | Status |
|-------|--------|
| Arsitektur SoC 4-Tier | ✅ Terverifikasi |
| SQL View (6 views) | ✅ Ter-deploy di PostgreSQL |
| LRU Cache (13 fungsi) | ✅ Semua ter-clear oleh invalidate_cache() |
| Parameterized Query | ✅ Semua f-string sudah diganti |
| Thread-safety set_demo_mode | ✅ Via threading.Lock() |
| Demo Mode fallback | ✅ Berfungsi tanpa PostgreSQL |
| Callback conflict | ✅ Semua ID unik global |
| SQL INNER JOIN → LEFT JOIN | ✅ Sudah diperbaiki dan re-deploy |
| Consistency score konsisten | ✅ SQL dan Python pakai formula sama |
| GitHub ready | ✅ .env dihapus dari history, setup.bat tersedia |
