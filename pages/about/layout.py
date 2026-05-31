# =============================================================================
# pages/about/layout.py — Halaman Tentang PaceFlow
# Berisi: info tim, arsitektur sistem, teknologi, referensi akademis
# Tidak ada callback, tidak ada query — pure static layout
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec, info_box
from layout.design_tokens import C, F, rgba

TEAM = [
    ("lucide:user", "Ammar Arifin",          "09040624081", "Ketua Tim"),
    ("lucide:user", "Che Mezofiona Azzahra", "09040624083", "Anggota"),
    ("lucide:user", "Afifah Nur Farida",     "09020624020", "Anggota"),
]

TECH = [
    ("lucide:database",   "PostgreSQL 16",   "Data layer — JOIN, agregasi, SQL View"),
    ("lucide:code",       "Python 3.10+",    "Bahasa pemrograman utama"),
    ("lucide:layout",     "Dash 4.1",        "Web framework — presentation layer"),
    ("lucide:bar-chart-2","Plotly 5.22",     "Library visualisasi interaktif"),
    ("lucide:link",       "SQLAlchemy 2.0",  "ORM dan connection pooling"),
    ("lucide:package",    "Pandas 2.2",      "Manipulasi data Python layer"),
]

STATS = [
    ("3",     "SQL Views",             C["blue"]),
    ("5",     "Tabel Relasional",      C["teal"]),
    ("1.024", "Race Entries",          C["green"]),
    ("1.726", "Pit Stop Records",      C["orange"]),
    ("1.021", "Qualifying Records",    C["red"]),
    ("1.083", "Driver Standings",      C["blue"]),
    ("28",    "Pembalap Unik",         C["teal"]),
    ("10",    "Konstruktor Unik",      C["green"]),
    ("1",     "Musim (2024)",          C["muted"]),
    ("24",    "Total Grand Prix",      C["red"]),
]

REFS = [
    ("lucide:book", C["red"],
     "Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly Media.",
     "Dasar arsitektur data pipeline dan optimasi query."),
    ("lucide:shield", C["blue"],
     "ISO/IEC 25010:2011. *Systems and Software Quality Requirements and Evaluation (SQuaRE)*.",
     "Standar kualitas perangkat lunak — kerangka evaluasi SoC PaceFlow."),
    ("lucide:cpu", C["teal"],
     "Hevner, A. R., et al. (2004). Design science in information systems research. *MIS Quarterly*, 28(1), 75–105.",
     "Metodologi Design Science Research yang digunakan sebagai paradigma penelitian."),
    ("lucide:layers", C["muted"],
     "Fowler, M. (2002). *Patterns of Enterprise Application Architecture*. Addison-Wesley.",
     "Repository Pattern yang diterapkan pada db.py."),
    ("lucide:bar-chart-2", C["orange"],
     "Bell, A., et al. (2016). Formula for success. *Journal of Quantitative Analysis in Sports*, 12(2), 99–112.",
     "Analisis statistik performa pembalap F1 — acuan pemilihan metrik KPI."),
    ("lucide:trending-up", C["blue"],
     "Montgomery, D. C. (2009). *Design and Analysis of Experiments* (7th ed.). Wiley.",
     "Metode repeated measures untuk benchmark performa (10 iterasi × 5 skenario)."),
]


def layout():
    return html.Div([
        sec("Tentang PaceFlow", "lucide:info"),

        dbc.Row([
            dbc.Col(card(html.Div([
                html.Div("PaceFlow", style=dict(
                    fontSize="28px", fontWeight="900",
                    color=C["text"], fontFamily=F, marginBottom="4px"
                )),
                html.Div("F1 Relational Analytics Dashboard", style=dict(
                    fontSize="13px", color=C["muted"],
                    fontFamily=F, marginBottom="16px"
                )),
                html.Div(
                    "PaceFlow adalah dashboard analitik Formula 1 yang dibangun "
                    "dengan arsitektur Separation of Concerns (SoC) sesuai ISO/IEC 25010. "
                    "Komputasi JOIN multi-tabel dieksekusi sepenuhnya di PostgreSQL "
                    "melalui SQL View terindeks, sehingga lapisan Dash hanya bertugas "
                    "merender data matang.",
                    style=dict(fontSize="13px", color=C["muted"],
                               lineHeight="1.7", fontFamily=F)
                ),
            ])), width=7),

            dbc.Col(card(html.Div([
                html.Div("Statistik Dataset", style=dict(
                    fontSize="11px", fontWeight="700", color=C["muted"],
                    letterSpacing="1px", textTransform="uppercase",
                    marginBottom="12px", fontFamily=F
                )),
                *[html.Div([
                    html.Span(v, style=dict(
                        fontSize="22px", fontWeight="900", color=c, fontFamily=F
                    )),
                    html.Span(f" {l}", style=dict(fontSize="12px", color=C["muted"], fontFamily=F)),
                ], style=dict(marginBottom="8px")) for v, l, c in STATS],
            ])), width=5),
        ], className="g-3"),

        sec("Tim Pengembang", "lucide:users"),
        card(dbc.Row([
            dbc.Col(html.Div([
                html.Div([
                    ico(ic, 18, C["blue"]),
                    html.Div([
                        html.Div(name, style=dict(fontSize="13px", fontWeight="700",
                                                   color=C["text"], fontFamily=F)),
                        html.Div(nim, style=dict(fontSize="11px", color=C["muted"], fontFamily=F)),
                        html.Div(role, style=dict(fontSize="10px", color=C["blue"],
                                                   fontFamily=F, fontWeight="600", marginTop="2px")),
                    ], style=dict(marginLeft="10px")),
                ], style=dict(display="flex", alignItems="center", marginBottom="16px"))
                for ic, name, nim, role in TEAM
            ]), width=6),
            dbc.Col(html.Div([
                html.Div("Program Studi", style=dict(fontSize="10px", fontWeight="700",
                    color=C["muted"], letterSpacing="1px", textTransform="uppercase",
                    marginBottom="6px", fontFamily=F)),
                html.Div("Sistem Informasi", style=dict(fontSize="14px", fontWeight="700",
                                                         color=C["text"], fontFamily=F)),
                html.Div("UIN Sunan Ampel Surabaya", style=dict(fontSize="12px",
                                                                  color=C["muted"], fontFamily=F, marginTop="3px")),
                html.Div("Tahun 2026", style=dict(fontSize="12px", color=C["muted"],
                                                   fontFamily=F, marginTop="2px")),
            ]), width=6),
        ], className="g-0")),

        sec("Arsitektur Sistem", "lucide:git-branch"),
        card(html.Div([
            html.Pre(
                "PostgreSQL (Data Layer)\n"
                "  └─ races · race_results · driver_standings\n"
                "  └─ pit_stops · qualifying\n"
                "  └─ INNER JOIN → v_f1_analytics\n"
                "           ↓\n"
                "SQLAlchemy + psycopg2 (Middleware)\n"
                "  └─ Repository Pattern · lru_cache\n"
                "  └─ Demo mode fallback otomatis\n"
                "           ↓\n"
                "Dash + Plotly (Presentation Layer)\n"
                "  └─ 6 halaman · Filter sidebar · Download CSV",
                style=dict(fontSize="12px", color=C["text"], fontFamily="monospace",
                           background=C["grid"], padding="16px", borderRadius="8px",
                           lineHeight="1.8", margin="0")
            ),
            html.Div("Prinsip: Separation of Concerns (SoC) — ISO/IEC 25010",
                style=dict(fontSize="11px", color=C["muted"], marginTop="10px", fontFamily=F)),
        ])),

        sec("Teknologi", "lucide:cpu"),
        card(dbc.Row([
            dbc.Col(html.Div([
                html.Div([
                    html.Div([ico(ic, 14, C["blue"]),
                        html.Span(name, style=dict(fontSize="12px", fontWeight="600",
                            color=C["text"], marginLeft="8px", fontFamily=F))],
                        style=dict(display="flex", alignItems="center", marginBottom="4px")),
                    html.Div(desc, style=dict(fontSize="11px", color=C["muted"],
                        marginLeft="22px", fontFamily=F, marginBottom="12px")),
                ]) for ic, name, desc in TECH[:3]
            ]), width=6),
            dbc.Col(html.Div([
                html.Div([
                    html.Div([ico(ic, 14, C["blue"]),
                        html.Span(name, style=dict(fontSize="12px", fontWeight="600",
                            color=C["text"], marginLeft="8px", fontFamily=F))],
                        style=dict(display="flex", alignItems="center", marginBottom="4px")),
                    html.Div(desc, style=dict(fontSize="11px", color=C["muted"],
                        marginLeft="22px", fontFamily=F, marginBottom="12px")),
                ]) for ic, name, desc in TECH[3:]
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
                        fontFamily=F, lineHeight="1.6", marginTop="4px", fontStyle="italic")),
                ]),
            ], style=dict(display="flex", alignItems="flex-start",
                padding="14px 16px", marginBottom="8px",
                background=C["grid"], borderRadius="8px",
                border=f"1px solid {C['border']}"))
            for i, (_, ic_color, ref_text, ref_note) in enumerate(REFS)]
        )),
    ])