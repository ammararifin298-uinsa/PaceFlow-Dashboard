# =============================================================================
# pages/about/layout.py — Halaman Tentang PaceFlow
# Berisi: info tim, statistik dinamis dari DB, arsitektur, teknologi, referensi
# Update: STATS dinamis dari DB via get_etl_info, arsitektur lebih detail
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec, info_box
from layout.design_tokens import C, F, rgba


TEAM = [
    ("lucide:user", "Ammar Arifin",          "09040624081", "Ketua Tim · R&D Lead"),
    ("lucide:user", "Che Mezofiona Azzahra", "09040624083", "Anggota · Frontend"),
    ("lucide:user", "Afifah Nur Farida",     "09020624020", "Anggota · Data Engineer"),
]

SUPERVISOR = [
    ("lucide:graduation-cap", "Khalid, M.Kom", "Dosen Pembimbing"),
]

TECH = [
    ("lucide:database",    "PostgreSQL 16",    "Data layer — SQL Views, JOIN, indeks, agregasi"),
    ("lucide:code",        "Python 3.12+",     "Bahasa pemrograman utama seluruh sistem"),
    ("lucide:layout",      "Dash 4.1",         "Web framework — presentation layer reaktif"),
    ("lucide:bar-chart-2", "Plotly 5.22",      "Library visualisasi interaktif berbasis WebGL"),
    ("lucide:link",        "SQLAlchemy 2.0",   "ORM, connection pooling, Repository Pattern"),
    ("lucide:package",     "Pandas 2.2",       "Transformasi dan formatting data output"),
    ("lucide:shield",      "Bootstrap 5",      "CSS framework — layout responsif komponen UI"),
    ("lucide:cloud",       "Railway",          "Cloud deployment — demo mode untuk evaluasi SUS"),
]

REFS = [
    ("lucide:book",        C["red"],
     "Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.",
     "Dasar arsitektur data pipeline, optimasi query, dan pemisahan lapisan komputasi."),
    ("lucide:shield",      C["blue"],
     "ISO/IEC 25010:2011. *Systems and Software Quality Requirements and Evaluation (SQuaRE)*.",
     "Standar kualitas perangkat lunak — kerangka evaluasi Separation of Concerns PaceFlow."),
    ("lucide:cpu",         C["teal"],
     "Hevner, A. R., et al. (2004). Design science in information systems research. *MIS Quarterly*, 28(1), 75–105.",
     "Metodologi Design Science Research sebagai paradigma penelitian Tugas Akhir."),
    ("lucide:layers",      C["muted"],
     "Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.",
     "Repository Pattern yang diterapkan pada db.py sebagai Data Access Layer."),
    ("lucide:bar-chart-2", C["orange"],
     "Bell, A., et al. (2016). Formula for success. *Journal of Quantitative Analysis in Sports*, 12(2), 99–112.",
     "Analisis statistik performa pembalap F1 — acuan pemilihan metrik KPI dashboard."),
    ("lucide:trending-up", C["blue"],
     "Montgomery, D. C. (2009). *Design and Analysis of Experiments* (7th ed.). Wiley.",
     "Metode repeated measures untuk benchmark performa (10 iterasi × 5 skenario query)."),
    ("lucide:users",       C["green"],
     "Brooke, J. (1996). SUS: A quick and dirty usability scale. *Usability Evaluation in Industry*, 189(194), 4–7.",
     "System Usability Scale (SUS) — instrumen evaluasi usability dashboard PaceFlow."),
    ("lucide:git-branch",  C["teal"],
     "Brown, S. (2015). *Software Architecture for Developers*. Leanpub.",
     "Modular Monolith sebagai pola arsitektur utama PaceFlow — dasar SoC implementasi."),
]


def layout():
    # ── Statistik dinamis dari DB ─────────────────────────────────────────────
    try:
        from db import get_etl_info
        from services.data_service import get_seasons, get_analytics
        import pandas as pd

        info    = get_etl_info()
        seasons = get_seasons()
        n_seasons      = len(seasons)
        total_entries  = int(info.get("total_entries", 0) or 0)
        total_races    = int(info.get("total_races", 0) or 0)

        # Hitung dari semua season
        all_dfs = [get_analytics(s) for s in seasons]
        df_all  = pd.concat([d for d in all_dfs if not d.empty], ignore_index=True) \
                  if all_dfs else pd.DataFrame()

        n_drivers      = int(df_all["driver_id"].nunique()) if not df_all.empty else 0
        n_constructors = int(df_all["constructor"].nunique()) if not df_all.empty else 0
        n_pit          = int(df_all["avg_pit_duration_s"].notna().sum()) if not df_all.empty else 0
        n_quali        = int(df_all["qualifying_pos"].notna().sum()) if not df_all.empty else 0

    except Exception:
        n_seasons      = 3
        total_entries  = 1024
        total_races    = 51
        n_drivers      = 28
        n_constructors = 11
        n_pit          = 1726
        n_quali        = 1021

    stats = [
        (str(n_seasons),          "Musim Tersedia",         C["blue"]),
        (str(total_races),        "Total Grand Prix",       C["red"]),
        (f"{total_entries:,}",    "Race Entries",           C["green"]),
        (str(n_drivers),          "Pembalap Unik",          C["teal"]),
        (str(n_constructors),     "Konstruktor Unik",       C["orange"]),
        (f"{n_pit:,}",            "Pit Stop Records",       C["blue"]),
        (f"{n_quali:,}",          "Qualifying Records",     C["teal"]),
        ("8",                     "Tabel Relasional",       C["muted"]),
        ("6",                     "SQL Views",              C["green"]),
        ("4",                     "Layer Arsitektur",       C["red"]),
    ]

    return html.Div([
        sec("Tentang PaceFlow", "lucide:info"),

        dbc.Row([
            dbc.Col(card(html.Div([
                html.Div([
                    html.Span("Pace", style=dict(fontSize="32px", fontWeight="900",
                        color=C["red"], fontFamily=F)),
                    html.Span("Flow", style=dict(fontSize="32px", fontWeight="900",
                        color=C["text"], fontFamily=F)),
                ], style=dict(marginBottom="4px")),
                html.Div("F1 Relational Analytics Dashboard", style=dict(
                    fontSize="13px", color=C["muted"], fontFamily=F, marginBottom="16px"
                )),
                html.Div(
                    "PaceFlow adalah dashboard analitik Formula 1 berbasis web yang "
                    "dibangun menggunakan arsitektur Modular Monolith dengan prinsip "
                    "Separation of Concerns (SoC) sesuai standar ISO/IEC 25010. "
                    "Seluruh komputasi berat — JOIN multi-tabel, agregasi statistik, "
                    "dan kalkulasi metrik — dieksekusi sepenuhnya di PostgreSQL melalui "
                    "6 SQL View terindeks. Lapisan Dash hanya bertugas merender data "
                    "matang, menghasilkan response time yang optimal.",
                    style=dict(fontSize="12px", color=C["muted"],
                               lineHeight="1.8", fontFamily=F, marginBottom="16px")
                ),
                html.Div([
                    html.Span("Metodologi: ", style=dict(fontWeight="700",
                        color=C["text"], fontSize="12px", fontFamily=F)),
                    html.Span("Design Science Research (Hevner, 2004)",
                        style=dict(color=C["muted"], fontSize="12px", fontFamily=F)),
                ], style=dict(marginBottom="6px")),
                html.Div([
                    html.Span("Standar: ", style=dict(fontWeight="700",
                        color=C["text"], fontSize="12px", fontFamily=F)),
                    html.Span("ISO/IEC 25010 · SUS Evaluation (Brooke, 1996)",
                        style=dict(color=C["muted"], fontSize="12px", fontFamily=F)),
                ], style=dict(marginBottom="6px")),
                html.Div([
                    html.Span("Target: ", style=dict(fontWeight="700",
                        color=C["text"], fontSize="12px", fontFamily=F)),
                    html.Span("Tugas Akhir S1 Sistem Informasi UINSA · 2026",
                        style=dict(color=C["muted"], fontSize="12px", fontFamily=F)),
                ]),
            ])), width=7),

            dbc.Col(card(html.Div([
                html.Div("Statistik Dataset", style=dict(
                    fontSize="10px", fontWeight="700", color=C["muted"],
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="12px", fontFamily=F
                )),
                *[html.Div([
                    html.Span(v, style=dict(
                        fontSize="20px", fontWeight="900", color=c, fontFamily=F
                    )),
                    html.Span(f"  {l}", style=dict(
                        fontSize="11px", color=C["muted"], fontFamily=F
                    )),
                ], style=dict(marginBottom="8px")) for v, l, c in stats],
            ])), width=5),
        ], className="g-3"),

        sec("Tim Pengembang", "lucide:users"),
        card(dbc.Row([
            dbc.Col(html.Div([
                html.Div("Mahasiswa", style=dict(
                    fontSize="10px", fontWeight="700", color=C["muted"],
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="12px", fontFamily=F
                )),
                *[html.Div([
                    ico(ic, 18, C["blue"]),
                    html.Div([
                        html.Div(name, style=dict(fontSize="13px", fontWeight="700",
                            color=C["text"], fontFamily=F)),
                        html.Div(nim, style=dict(fontSize="11px",
                            color=C["muted"], fontFamily=F)),
                        html.Div(role, style=dict(fontSize="10px", color=C["blue"],
                            fontFamily=F, fontWeight="600", marginTop="2px")),
                    ], style=dict(marginLeft="10px")),
                ], style=dict(display="flex", alignItems="center", marginBottom="16px"))
                for ic, name, nim, role in TEAM],
            ]), width=6),
            dbc.Col(html.Div([
                html.Div("Dosen Pembimbing", style=dict(
                    fontSize="10px", fontWeight="700", color=C["muted"],
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="12px", fontFamily=F
                )),
                *[html.Div([
                    ico(ic, 18, C["orange"]),
                    html.Div([
                        html.Div(name, style=dict(fontSize="13px", fontWeight="700",
                            color=C["text"], fontFamily=F)),
                        html.Div(role, style=dict(fontSize="11px",
                            color=C["muted"], fontFamily=F)),
                    ], style=dict(marginLeft="10px")),
                ], style=dict(display="flex", alignItems="center", marginBottom="16px"))
                for ic, name, role in SUPERVISOR],
                html.Div([
                    html.Div("Program Studi", style=dict(fontSize="10px", fontWeight="700",
                        color=C["muted"], letterSpacing="1px", textTransform="uppercase",
                        marginBottom="6px", fontFamily=F)),
                    html.Div("Sistem Informasi", style=dict(fontSize="14px",
                        fontWeight="700", color=C["text"], fontFamily=F)),
                    html.Div("UIN Sunan Ampel Surabaya", style=dict(fontSize="12px",
                        color=C["muted"], fontFamily=F, marginTop="3px")),
                    html.Div("Angkatan 2024 · Lulus 2028", style=dict(fontSize="12px",
                        color=C["muted"], fontFamily=F, marginTop="2px")),
                ], style=dict(marginTop="8px")),
            ]), width=6),
        ], className="g-0")),

        sec("Arsitektur Sistem", "lucide:git-branch"),
        card(html.Div([
            dbc.Row([
                dbc.Col(html.Div([
                    # Layer 0: Database
                    html.Div([
                        html.Div([
                            html.Div("LAYER 0", style=dict(
                                fontSize="9px", fontWeight="800", color="#FFF",
                                background=C["red"], padding="2px 8px", borderRadius="4px",
                                fontFamily=F, letterSpacing="0.5px"
                            )),
                            html.Div("DATABASE (PERSISTENCE LAYER)", style=dict(
                                fontSize="12px", fontWeight="800", color=C["text"],
                                marginLeft="10px", fontFamily=F, letterSpacing="0.5px"
                            )),
                        ], style=dict(display="flex", alignItems="center", marginBottom="8px")),
                        html.Div("PostgreSQL 16 · 8 Tabel Relasional · 6 Views Terindeks", style=dict(
                            fontSize="10px", fontWeight="700", color=C["red"],
                            fontFamily=F, marginBottom="6px"
                        )),
                        html.Div("Menyimpan seluruh dataset Formula 1. Komputasi berat (JOIN, aggregasi, window functions) didelegasikan langsung ke SQL Views (v_f1_analytics, v_kpi_summary, v_dnf_causes, v_championship_progression, v_constructor_season, v_driver_season_summary) agar response time optimal.", style=dict(
                            fontSize="11px", color=C["muted"], fontFamily=F, lineHeight="1.5"
                        ))
                    ], style=dict(
                        background=C["surface"], border=f"1px solid {C['border']}",
                        borderLeft=f"4px solid {C['red']}", borderRadius="8px",
                        padding="12px 16px", boxShadow="0 1px 3px rgba(0,0,0,0.05)"
                    )),

                    # Arrow 1
                    html.Div([
                        html.Div(style=dict(width="2px", height="16px", background=C["border"], margin="0 auto")),
                        html.Div("psycopg2 driver connection", style=dict(
                            background=C["grid"], border=f"1px solid {C['border']}",
                            borderRadius="12px", padding="2px 10px", fontSize="9px",
                            fontWeight="600", color=C["muted"], fontFamily=F,
                            display="inline-block", marginTop="-6px", marginBottom="-6px",
                            zIndex=2, position="relative"
                        )),
                        html.Div(style=dict(
                            width="0", height="0", borderLeft="5px solid transparent",
                            borderRight="5px solid transparent", borderTop=f"6px solid {C['border']}",
                            margin="0 auto"
                        )),
                    ], style=dict(display="flex", flexDirection="column", alignItems="center", margin="2px 0")),

                    # Layer 1: DAL
                    html.Div([
                        html.Div([
                            html.Div("LAYER 1", style=dict(
                                fontSize="9px", fontWeight="800", color="#FFF",
                                background=C["teal"], padding="2px 8px", borderRadius="4px",
                                fontFamily=F, letterSpacing="0.5px"
                            )),
                            html.Div("DATA ACCESS LAYER (DAL)", style=dict(
                                fontSize="12px", fontWeight="800", color=C["text"],
                                marginLeft="10px", fontFamily=F, letterSpacing="0.5px"
                            )),
                        ], style=dict(display="flex", alignItems="center", marginBottom="8px")),
                        html.Div("db.py · demo_data.py · SQLAlchemy 2.0 · Python lru_cache", style=dict(
                            fontSize="10px", fontWeight="700", color=C["teal"],
                            fontFamily=F, marginBottom="6px"
                        )),
                        html.Div("Repository Pattern sebagai pintu gerbang akses data terpusat. Mengimplementasikan caching memori dengan lru_cache untuk response time ultra-cepat, serta mekanisme Demo Mode Fallback (otomatis membaca demo_cache.csv jika koneksi DB offline).", style=dict(
                            fontSize="11px", color=C["muted"], fontFamily=F, lineHeight="1.5"
                        ))
                    ], style=dict(
                        background=C["surface"], border=f"1px solid {C['border']}",
                        borderLeft=f"4px solid {C['teal']}", borderRadius="8px",
                        padding="12px 16px", boxShadow="0 1px 3px rgba(0,0,0,0.05)"
                    )),

                    # Arrow 2
                    html.Div([
                        html.Div(style=dict(width="2px", height="16px", background=C["border"], margin="0 auto")),
                        html.Div("Pandas DataFrame output", style=dict(
                            background=C["grid"], border=f"1px solid {C['border']}",
                            borderRadius="12px", padding="2px 10px", fontSize="9px",
                            fontWeight="600", color=C["muted"], fontFamily=F,
                            display="inline-block", marginTop="-6px", marginBottom="-6px",
                            zIndex=2, position="relative"
                        )),
                        html.Div(style=dict(
                            width="0", height="0", borderLeft="5px solid transparent",
                            borderRight="5px solid transparent", borderTop=f"6px solid {C['border']}",
                            margin="0 auto"
                        )),
                    ], style=dict(display="flex", flexDirection="column", alignItems="center", margin="2px 0")),

                    # Layer 2: Service
                    html.Div([
                        html.Div([
                            html.Div("LAYER 2", style=dict(
                                fontSize="9px", fontWeight="800", color="#FFF",
                                background=C["orange"], padding="2px 8px", borderRadius="4px",
                                fontFamily=F, letterSpacing="0.5px"
                            )),
                            html.Div("SERVICE LAYER (BUSINESS LOGIC)", style=dict(
                                fontSize="12px", fontWeight="800", color=C["text"],
                                marginLeft="10px", fontFamily=F, letterSpacing="0.5px"
                            )),
                        ], style=dict(display="flex", alignItems="center", marginBottom="8px")),
                        html.Div("data_service.py · Schema Enforcement · Cache Invalidation", style=dict(
                            fontSize="10px", fontWeight="700", color=C["orange"],
                            fontFamily=F, marginBottom="6px"
                        )),
                        html.Div("Mengelola logika bisnis utama: penegakan skema data wajib (enforce_schema), pembersihan cache (invalidate_cache) setelah reload dataset di halaman Benchmark, serta manajemen toggle mode running.", style=dict(
                            fontSize="11px", color=C["muted"], fontFamily=F, lineHeight="1.5"
                        ))
                    ], style=dict(
                        background=C["surface"], border=f"1px solid {C['border']}",
                        borderLeft=f"4px solid {C['orange']}", borderRadius="8px",
                        padding="12px 16px", boxShadow="0 1px 3px rgba(0,0,0,0.05)"
                    )),

                    # Arrow 3
                    html.Div([
                        html.Div(style=dict(width="2px", height="16px", background=C["border"], margin="0 auto")),
                        html.Div("Python dict / Pandas DataFrame", style=dict(
                            background=C["grid"], border=f"1px solid {C['border']}",
                            borderRadius="12px", padding="2px 10px", fontSize="9px",
                            fontWeight="600", color=C["muted"], fontFamily=F,
                            display="inline-block", marginTop="-6px", marginBottom="-6px",
                            zIndex=2, position="relative"
                        )),
                        html.Div(style=dict(
                            width="0", height="0", borderLeft="5px solid transparent",
                            borderRight="5px solid transparent", borderTop=f"6px solid {C['border']}",
                            margin="0 auto"
                        )),
                    ], style=dict(display="flex", flexDirection="column", alignItems="center", margin="2px 0")),

                    # Layer 3: Presentation
                    html.Div([
                        html.Div([
                            html.Div("LAYER 3", style=dict(
                                fontSize="9px", fontWeight="800", color="#FFF",
                                background=C["blue"], padding="2px 8px", borderRadius="4px",
                                fontFamily=F, letterSpacing="0.5px"
                            )),
                            html.Div("PRESENTATION LAYER (USER INTERFACE)", style=dict(
                                fontSize="12px", fontWeight="800", color=C["text"],
                                marginLeft="10px", fontFamily=F, letterSpacing="0.5px"
                            )),
                        ], style=dict(display="flex", alignItems="center", marginBottom="8px")),
                        html.Div("Dash 4.1 · Plotly 5.22 · Bootstrap 5 · DashIconify", style=dict(
                            fontSize="10px", fontWeight="700", color=C["blue"],
                            fontFamily=F, marginBottom="6px"
                        )),
                        html.Div("Antarmuka pengguna interaktif (7 halaman utama: Beranda, Klasemen, Analitik, H2H, Tabel Data, Perbandingan, Benchmark) yang merender data matang menjadi visualisasi premium.", style=dict(
                            fontSize="11px", color=C["muted"], fontFamily=F, lineHeight="1.5"
                        ))
                    ], style=dict(
                        background=C["surface"], border=f"1px solid {C['border']}",
                        borderLeft=f"4px solid {C['blue']}", borderRadius="8px",
                        padding="12px 16px", boxShadow="0 1px 3px rgba(0,0,0,0.05)"
                    )),
                ]), width=7),
                dbc.Col(html.Div([
                    html.Div("Prinsip Desain", style=dict(
                        fontSize="10px", fontWeight="700", color=C["muted"],
                        letterSpacing="1px", textTransform="uppercase",
                        marginBottom="12px", fontFamily=F
                    )),
                    *[html.Div([
                        html.Div(style=dict(width="6px", height="6px",
                            borderRadius="50%", background=c,
                            marginTop="5px", marginRight="10px", flexShrink="0")),
                        html.Div([
                            html.Div(title, style=dict(fontSize="12px",
                                fontWeight="700", color=C["text"], fontFamily=F)),
                            html.Div(desc, style=dict(fontSize="11px",
                                color=C["muted"], fontFamily=F, lineHeight="1.5")),
                        ]),
                    ], style=dict(display="flex", marginBottom="12px"))
                    for title, desc, c in [
                        ("Separation of Concerns",
                         "Komputasi di DB, formatting di Pandas, rendering di Dash",
                         C["blue"]),
                        ("Repository Pattern",
                         "db.py sebagai satu-satunya pintu akses ke PostgreSQL",
                         C["teal"]),
                        ("Demo Mode Fallback",
                         "Auto-switch ke demo_cache.csv jika PostgreSQL tidak tersedia",
                         C["green"]),
                        ("Modular Monolith",
                         "Satu deployment, modul terpisah per halaman dan layer",
                         C["orange"]),
                        ("ISO/IEC 25010",
                         "Standar kualitas perangkat lunak sebagai kerangka evaluasi",
                         C["red"]),
                    ]],
                ]), width=5),
            ], className="g-3"),
        ])),

        sec("Teknologi", "lucide:cpu"),
        card(dbc.Row([
            dbc.Col(html.Div([
                html.Div([
                    html.Div([
                        ico(ic, 14, C["blue"]),
                        html.Span(name, style=dict(fontSize="12px", fontWeight="600",
                            color=C["text"], marginLeft="8px", fontFamily=F)),
                    ], style=dict(display="flex", alignItems="center", marginBottom="4px")),
                    html.Div(desc, style=dict(fontSize="11px", color=C["muted"],
                        marginLeft="22px", fontFamily=F, marginBottom="12px")),
                ]) for ic, name, desc in TECH[:4]
            ]), width=6),
            dbc.Col(html.Div([
                html.Div([
                    html.Div([
                        ico(ic, 14, C["blue"]),
                        html.Span(name, style=dict(fontSize="12px", fontWeight="600",
                            color=C["text"], marginLeft="8px", fontFamily=F)),
                    ], style=dict(display="flex", alignItems="center", marginBottom="4px")),
                    html.Div(desc, style=dict(fontSize="11px", color=C["muted"],
                        marginLeft="22px", fontFamily=F, marginBottom="12px")),
                ]) for ic, name, desc in TECH[4:]
            ]), width=6),
        ], className="g-0")),

        sec("Referensi Akademis", "lucide:book-open"),
        card(html.Div(
            [html.Div(
                f"Terdapat {len(REFS)} referensi yang digunakan dalam penelitian ini.",
                style=dict(fontSize="12px", color=C["muted"], fontFamily=F,
                           lineHeight="1.7", marginBottom="20px",
                           padding="10px 14px", background=rgba(C["blue"], 0.05),
                           borderRadius="6px", borderLeft=f"3px solid {C['blue']}")
            )] +
            [html.Div([
                html.Div([
                    html.Div(str(i+1), style=dict(fontSize="10px", fontWeight="900",
                        color="#FFF", fontFamily=F)),
                ], style=dict(width="22px", height="22px", borderRadius="50%",
                    background=ic_color, display="flex", alignItems="center",
                    justifyContent="center", flexShrink="0",
                    marginRight="14px", marginTop="2px")),
                html.Div([
                    dcc.Markdown(ref_text, style=dict(fontSize="12px", color=C["text"],
                        fontFamily=F, lineHeight="1.75", margin="0")),
                    html.Div(ref_note, style=dict(fontSize="11px", color=C["muted"],
                        fontFamily=F, lineHeight="1.6", marginTop="4px",
                        fontStyle="italic")),
                ]),
            ], style=dict(display="flex", alignItems="flex-start",
                padding="14px 16px", marginBottom="8px",
                background=C["grid"], borderRadius="8px",
                border=f"1px solid {C['border']}"))
            for i, (_, ic_color, ref_text, ref_note) in enumerate(REFS)]
        )),
    ])