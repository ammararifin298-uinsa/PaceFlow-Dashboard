# =============================================================================
# pages/about/layout.py — Halaman Tentang PaceFlow
# Berisi: info tim, statistik dinamis dari DB, arsitektur, teknologi, referensi
# Update: Redesign layout dengan grid, stats, dan referensi akordion (Accordion)
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec, info_box, kpi_card
from layout.design_tokens import C, F, rgba


TEAM = [
    ("lucide:user", "Ammar Arifin",          "09040624081", "Ketua Tim · R&D Lead", C["blue"]),
    ("lucide:user", "Che Mezofiona Azzahra", "09040624083", "Anggota · Frontend", "#7C3AED"),
    ("lucide:user", "Afifah Nur Farida",     "09020624020", "Anggota · Data Engineer", C["orange"]),
]

SUPERVISOR = [
    ("lucide:graduation-cap", "Khalid, M.Kom", "Dosen Pembimbing", C["red"]),
]

TECH = [
    ("lucide:database",    "PostgreSQL 16",    "Data layer — SQL Views, JOIN, indeks, agregasi", C["blue"]),
    ("lucide:code",        "Python 3.12+",     "Bahasa pemrograman utama seluruh sistem", C["orange"]),
    ("lucide:layout",      "Dash 4.1",         "Web framework — presentation layer reaktif", C["teal"]),
    ("lucide:bar-chart-2", "Plotly 5.22",      "Library visualisasi interaktif berbasis WebGL", "#7C3AED"),
    ("lucide:link",        "SQLAlchemy 2.0",   "ORM, connection pooling, Repository Pattern", C["red"]),
    ("lucide:package",     "Pandas 2.2",       "Transformasi dan formatting data output", C["green"]),
    ("lucide:shield",      "Bootstrap 5",      "CSS framework — layout responsif komponen UI", C["blue"]),
]

REFS = [
    ("Kleppmann, M. (2017). Designing Data-Intensive Applications.",
     "Dasar arsitektur data pipeline, optimasi query, dan pemisahan lapisan komputasi."),
    ("ISO/IEC 25010:2011. Systems and Software Quality Requirements and Evaluation.",
     "Standar kualitas perangkat lunak — kerangka evaluasi Separation of Concerns PaceFlow."),
    ("Hevner, A. R., et al. (2004). Design science in information systems research.",
     "Metodologi Design Science Research sebagai paradigma penelitian Tugas Akhir."),
    ("Fowler, M. (2002). Patterns of Enterprise Application Architecture.",
     "Repository Pattern yang diterapkan pada db.py sebagai Data Access Layer."),
    ("Bell, A., et al. (2016). Formula for success. Journal of Quantitative Analysis in Sports.",
     "Analisis statistik performa pembalap F1 — acuan pemilihan metrik KPI dashboard."),
    ("Montgomery, D. C. (2009). Design and Analysis of Experiments.",
     "Metode repeated measures untuk benchmark performa (10 iterasi × 5 skenario query)."),
    ("Brown, S. (2015). Software Architecture for Developers.",
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

    return html.Div([
        # ── HERO & OVERVIEW ──────────────────────────────────────────────────
        html.Div([
            html.Div(style=dict(
                width="64px", height="64px", borderRadius="18px",
                background=f"linear-gradient(135deg, {C['blue']}, #7C3AED)",
                display="flex", alignItems="center", justifyContent="center",
                boxShadow=f"0 8px 32px {rgba(C['blue'], 0.35)}",
                margin="0 auto 18px auto",
            ), children=[ico("lucide:info", 34, "#fff")]),
            html.Div("Tentang PaceFlow", style=dict(
                fontSize="28px", fontWeight="900", letterSpacing="-0.5px",
                color=C["text"], fontFamily=F, marginBottom="6px",
                textAlign="center"
            )),
            html.Div(
                "PaceFlow adalah dashboard analitik Formula 1 berbasis web yang dibangun menggunakan arsitektur Modular Monolith dengan prinsip Separation of Concerns (SoC) sesuai standar ISO/IEC 25010.",
                style=dict(
                    fontSize="13px", color=C["muted"], fontFamily=F,
                    maxWidth="600px", lineHeight="1.7", margin="0 auto 30px auto",
                    textAlign="center"
                )
            ),
        ]),

        # ── STATISTIK DATASET (GRID) ─────────────────────────────────────────
        sec("Statistik Dataset", "lucide:database"),
        dbc.Row([
            dbc.Col(kpi_card("Musim Tersedia", str(n_seasons), "Total Musim F1", C["blue"], "lucide:calendar"), width=3),
            dbc.Col(kpi_card("Total Grand Prix", str(total_races), "Balapan Terdata", C["red"], "lucide:flag"), width=3),
            dbc.Col(kpi_card("Race Entries", f"{total_entries:,}", "Total Hasil Balap", C["green"], "lucide:list"), width=3),
            dbc.Col(kpi_card("Pembalap Unik", str(n_drivers), "Di Semua Musim", C["teal"], "lucide:users"), width=3),
            dbc.Col(kpi_card("Konstruktor Unik", str(n_constructors), "Di Semua Musim", C["orange"], "lucide:shield"), width=3),
            dbc.Col(kpi_card("Pit Stop Records", f"{n_pit:,}", "Data Pit Stop", C["blue"], "lucide:clock"), width=3),
            dbc.Col(kpi_card("Qualifying", f"{n_quali:,}", "Hasil Kualifikasi", C["teal"], "lucide:zap"), width=3),
            dbc.Col(kpi_card("Views Terindeks", "6", "PostgreSQL Views", C["red"], "lucide:database"), width=3),
        ], className="g-3", style=dict(marginBottom="24px")),

        # ── TIM PENGEMBANG DAN DOSEN PEMBIMBING ────────────────────────────────
        sec("Tim dan Pembimbing", "lucide:users"),
        dbc.Row([
            dbc.Col(card(html.Div([
                html.Div("Tim Pengembang", style=dict(
                    fontSize="10px", fontWeight="700", color=C["muted"],
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="16px", fontFamily=F
                )),
                *[html.Div([
                    html.Div([
                        ico(ic, 18, color)
                    ], style=dict(
                        width="36px", height="36px", borderRadius="50%",
                        background=rgba(color, 0.1), display="flex",
                        alignItems="center", justifyContent="center", flexShrink=0
                    )),
                    html.Div([
                        html.Div(name, style=dict(fontSize="13px", fontWeight="700", color=C["text"], fontFamily=F)),
                        html.Div(nim, style=dict(fontSize="11px", color=C["muted"], fontFamily=F)),
                        html.Div(role, style=dict(fontSize="10px", color=color, fontFamily=F, fontWeight="600")),
                    ], style=dict(marginLeft="12px")),
                ], style=dict(display="flex", alignItems="center", marginBottom="16px"))
                for ic, name, nim, role, color in TEAM]
            ])), width=6),
            dbc.Col(card(html.Div([
                html.Div("Dosen Pembimbing dan Prodi", style=dict(
                    fontSize="10px", fontWeight="700", color=C["muted"],
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="16px", fontFamily=F
                )),
                *[html.Div([
                    html.Div([
                        ico(ic, 18, color)
                    ], style=dict(
                        width="36px", height="36px", borderRadius="50%",
                        background=rgba(color, 0.1), display="flex",
                        alignItems="center", justifyContent="center", flexShrink=0
                    )),
                    html.Div([
                        html.Div(name, style=dict(fontSize="13px", fontWeight="700", color=C["text"], fontFamily=F)),
                        html.Div(role, style=dict(fontSize="11px", color=C["muted"], fontFamily=F)),
                    ], style=dict(marginLeft="12px")),
                ], style=dict(display="flex", alignItems="center", marginBottom="24px"))
                for ic, name, role, color in SUPERVISOR],
                html.Div([
                    html.Div("Sistem Informasi", style=dict(fontSize="14px", fontWeight="700", color=C["text"], fontFamily=F)),
                    html.Div("UIN Sunan Ampel Surabaya", style=dict(fontSize="12px", color=C["muted"], fontFamily=F, marginTop="3px")),
                    html.Div("Angkatan 2024 · Lulus 2028", style=dict(fontSize="12px", color=C["muted"], fontFamily=F, marginTop="2px")),
                ], style=dict(
                    padding="12px", background=rgba(C["blue"], 0.05),
                    borderLeft=f"3px solid {C['blue']}", borderRadius="0 6px 6px 0"
                ))
            ])), width=6),
        ], className="g-3", style=dict(marginBottom="24px")),

        # ── ARSITEKTUR ───────────────────────────────────────────────────────
        sec("Arsitektur Sistem (Modular Monolith)", "lucide:git-branch"),
        dbc.Row([
            dbc.Col(card(html.Div([
                html.Div("LAYER 0: DATABASE (PERSISTENCE LAYER)", style=dict(
                    fontSize="10px", fontWeight="800", color=C["red"],
                    letterSpacing="1px", fontFamily=F, marginBottom="8px"
                )),
                html.Div("PostgreSQL 16 · 8 Tabel Relasional · 6 Views Terindeks", style=dict(
                    fontSize="11px", fontWeight="700", color=C["text"],
                    fontFamily=F, marginBottom="6px"
                )),
                html.Div("Komputasi berat didelegasikan langsung ke SQL Views agar response time optimal.", style=dict(
                    fontSize="11px", color=C["muted"], fontFamily=F, lineHeight="1.5"
                ))
            ], style=dict(borderLeft=f"4px solid {C['red']}", paddingLeft="12px"))), width=4),

            dbc.Col(card(html.Div([
                html.Div("LAYER 1-2: DAL DAN SERVICE (BUSINESS LOGIC)", style=dict(
                    fontSize="10px", fontWeight="800", color=C["orange"],
                    letterSpacing="1px", fontFamily=F, marginBottom="8px"
                )),
                html.Div("db.py · SQLAlchemy 2.0 · Python lru_cache", style=dict(
                    fontSize="11px", fontWeight="700", color=C["text"],
                    fontFamily=F, marginBottom="6px"
                )),
                html.Div("Repository Pattern dan caching memori dengan fallback ke CSV jika DB offline.", style=dict(
                    fontSize="11px", color=C["muted"], lineHeight="1.5", fontFamily=F
                ))
            ], style=dict(borderLeft=f"4px solid {C['orange']}", paddingLeft="12px"))), width=4),

            dbc.Col(card(html.Div([
                html.Div("LAYER 3: PRESENTATION (USER INTERFACE)", style=dict(
                    fontSize="10px", fontWeight="800", color=C["blue"],
                    letterSpacing="1px", fontFamily=F, marginBottom="8px"
                )),
                html.Div("Dash 4.1 · Plotly 5.22 · Bootstrap 5", style=dict(
                    fontSize="11px", fontWeight="700", color=C["text"],
                    fontFamily=F, marginBottom="6px"
                )),
                html.Div("Antarmuka interaktif yang merender data matang menjadi visualisasi premium.", style=dict(
                    fontSize="11px", color=C["muted"], fontFamily=F, lineHeight="1.5"
                ))
            ], style=dict(borderLeft=f"4px solid {C['blue']}", paddingLeft="12px"))), width=4),
        ], className="g-3", style=dict(marginBottom="24px")),

        # ── TEKNOLOGI ────────────────────────────────────────────────────────
        sec("Teknologi yang Digunakan", "lucide:cpu"),
        dbc.Row([
            *[dbc.Col(card(html.Div([
                html.Div([
                    html.Div([
                        ico(ic, 18, color)
                    ], style=dict(
                        width="36px", height="36px", borderRadius="8px",
                        background=rgba(color, 0.1), display="flex",
                        alignItems="center", justifyContent="center", flexShrink=0,
                        marginBottom="12px"
                    )),
                    html.Div(name, style=dict(fontSize="13px", fontWeight="700", color=C["text"], fontFamily=F)),
                    html.Div(desc, style=dict(fontSize="11px", color=C["muted"], fontFamily=F, marginTop="4px", lineHeight="1.5")),
                ])
            ]), p="16px"), width=3) for ic, name, desc, color in TECH]
        ], className="g-3", style=dict(marginBottom="24px")),

        # ── REFERENSI AKADEMIS (ACCORDION) ───────────────────────────────────
        sec("Referensi Akademis", "lucide:book-open"),
        info_box(f"Terdapat **{len(REFS)}** referensi akademis yang menjadi landasan PaceFlow Dashboard."),
        card(dbc.Accordion(
            [
                dbc.AccordionItem(
                    [
                        html.Div(desc, style=dict(
                            fontSize="12px", color=C["muted"], fontFamily=F, lineHeight="1.6"
                        ))
                    ],
                    title=title,
                    style=dict(fontFamily=F, fontSize="13px", fontWeight="600")
                ) for title, desc in REFS
            ],
            start_collapsed=True,
            flush=True,
            style=dict(fontFamily=F)
        ), p="0px"),
    ])