# =============================================================================
# pages/settings/layout.py — Halaman Settings PaceFlow
# Fix: hapus dcc.Download(dl-backup) duplikat, ganti & → dan
# mode-indicator sekarang diisi reaktif oleh callback, bukan static Python
# =============================================================================

from dash import html, dcc  # dcc tetap dipakai untuk dcc.Upload dan dcc.Loading
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec, info_box
from layout.design_tokens import C, F, rgba


def layout():
    return html.Div([
        sec("Pengaturan", "lucide:settings"),

        # ── Koneksi Database ─────────────────────────────────────────────────
        sec("Koneksi Database", "lucide:database"),
        card(
            html.Div([
                dbc.Row([
                    dbc.Col(html.Div([
                        html.Div("MODE SAAT INI", style=dict(
                            fontSize="9px", fontWeight="700", letterSpacing="1.5px",
                            textTransform="uppercase", color=C["muted"],
                            marginBottom="6px", fontFamily=F)),
                        # Diisi oleh callback update_mode_indicator — reaktif
                        html.Div(id="mode-indicator"),
                    ]), width=6),
                    dbc.Col(html.Div([
                        html.Div("TOGGLE MODE", style=dict(
                            fontSize="9px", fontWeight="700", letterSpacing="1.5px",
                            textTransform="uppercase", color=C["muted"],
                            marginBottom="6px", fontFamily=F)),
                        html.Button([
                            ico("lucide:refresh-cw", 13, "#FFF"),
                            html.Span(
                                " Toggle PostgreSQL / Demo",
                                style=dict(marginLeft="6px")),
                        ], id="btn-toggle-mode", n_clicks=0,
                        style=dict(
                            display="flex", alignItems="center",
                            background=C["blue"],
                            color="#FFF", border="none", borderRadius="6px",
                            padding="8px 16px", fontSize="11px", fontWeight="600",
                            fontFamily=F, cursor="pointer")),
                    ]), width=6),
                ], className="g-3"),
                html.Div(id="toggle-mode-result", style=dict(marginTop="12px")),
            ])
        ),

        # ── Database Health ──────────────────────────────────────────────────
        sec("Status Database", "lucide:activity"),
        card(html.Div([
            html.Button([
                ico("lucide:refresh-cw", 13, "#FFF"),
                html.Span(" Cek Koneksi", style=dict(marginLeft="6px")),
            ], id="btn-db-health", n_clicks=0,
            style=dict(display="flex", alignItems="center",
                       background=C["blue"], color="#FFF",
                       border="none", borderRadius="6px",
                       padding="8px 16px", fontSize="11px",
                       fontWeight="600", fontFamily=F,
                       cursor="pointer", marginBottom="12px")),
            dcc.Loading(
                html.Div(id="db-health-result"),
                type="dot", color=C["blue"],
            ),
        ])),

        # ── Cache Management ─────────────────────────────────────────────────
        sec("Cache", "lucide:zap"),
        card(html.Div([
            html.Div("Cache menyimpan hasil query terakhir untuk mempercepat loading. "
                     "Invalidate cache setelah upload data baru.",
                style=dict(fontSize="12px", color=C["muted"],
                           fontFamily=F, marginBottom="12px")),
            html.Button([
                ico("lucide:trash-2", 13, "#FFF"),
                html.Span(" Clear Cache", style=dict(marginLeft="6px")),
            ], id="btn-clear-cache", n_clicks=0,
            style=dict(display="flex", alignItems="center",
                       background=C["red"], color="#FFF",
                       border="none", borderRadius="6px",
                       padding="8px 16px", fontSize="11px",
                       fontWeight="600", fontFamily=F, cursor="pointer")),
            dcc.Loading(
                html.Div(id="clear-cache-result", style=dict(marginTop="12px")),
                type="dot", color=C["green"],
            ),
        ])),

        # ── Upload CSV ───────────────────────────────────────────────────────
        sec("Upload Data CSV", "lucide:upload"),
        card(html.Div([
            info_box("Upload file CSV untuk update data. Format harus sesuai skema "
                     "yang ada di folder `Data/`. Setelah upload, jalankan ETL ulang.",
                     C["orange"]),
            dcc.Upload(
                id="upload-csv",
                children=html.Div([
                    ico("lucide:upload-cloud", 24, C["muted"]),
                    html.Div("Drag dan Drop atau Klik untuk Upload CSV",
                        style=dict(fontSize="12px", color=C["muted"],
                                   fontFamily=F, marginTop="8px")),
                    html.Div("Format: races.csv, race_results.csv, dll.",
                        style=dict(fontSize="10px", color=C["muted"],
                                   fontFamily=F, marginTop="4px")),
                ], style=dict(textAlign="center", padding="20px")),
                style=dict(
                    border=f"2px dashed {C['border']}", borderRadius="8px",
                    cursor="pointer", background=C["grid"],
                    marginBottom="12px"
                ),
                multiple=False,
            ),
            dcc.Loading(
                html.Div(id="upload-csv-result"),
                type="dot", color=C["blue"],
            ),
            html.Div([
                html.Button([
                    ico("lucide:database", 13, "#FFF"),
                    html.Span(" Jalankan Sinkronisasi Database (ETL)", style=dict(marginLeft="6px")),
                ], id="btn-run-etl", n_clicks=0,
                style=dict(display="flex", alignItems="center",
                           background=C["green"], color="#FFF",
                           border="none", borderRadius="6px",
                           padding="8px 16px", fontSize="11px",
                           fontWeight="600", fontFamily=F,
                           cursor="pointer", marginTop="12px")),
                dcc.Loading(
                    html.Div(id="run-etl-result", style=dict(marginTop="12px")),
                    type="dot", color=C["green"],
                ),
            ], style=dict(borderTop=f"1px solid {C['border']}", paddingTop="12px", marginTop="12px")),
        ])),

        # ── ETL dan Data Info ────────────────────────────────────────────────
        sec("ETL dan Data Info", "lucide:terminal"),
        card(html.Div([
            html.Button([
                ico("lucide:refresh-cw", 13, "#FFF"),
                html.Span(" Refresh Info", style=dict(marginLeft="6px")),
            ], id="btn-etl-info", n_clicks=0,
            style=dict(display="flex", alignItems="center",
                       background=C["teal"], color="#FFF",
                       border="none", borderRadius="6px",
                       padding="8px 16px", fontSize="11px",
                       fontWeight="600", fontFamily=F,
                       cursor="pointer", marginBottom="12px")),
            dcc.Loading(
                html.Div(id="etl-info-result"),
                type="dot", color=C["teal"],
            ),
        ])),



        # ── App Info ─────────────────────────────────────────────────────────
        sec("Informasi Aplikasi", "lucide:info"),
        card(html.Div([
            *[html.Div([
                html.Span(label, style=dict(fontSize="11px", fontWeight="700",
                    color=C["muted"], fontFamily=F, width="160px",
                    display="inline-block")),
                html.Span(value, style=dict(fontSize="11px",
                    color=C["text"], fontFamily=F)),
            ], style=dict(marginBottom="8px"))
            for label, value in [
                ("Versi",           "PaceFlow v1.0.0"),
                ("Framework",       "Python Dash 2.x"),
                ("Database",        "PostgreSQL 16"),
                ("Arsitektur",      "Modular Monolith · SoC"),
                ("Standar",         "ISO/IEC 25010"),
                ("Metodologi",      "Design Science Research"),
                ("Institusi",       "UIN Sunan Ampel Surabaya"),
                ("Tahun",           "2026"),
            ]],
        ])),
    ])