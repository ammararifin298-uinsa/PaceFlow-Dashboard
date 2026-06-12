# =============================================================================
# pages/comparison/layout.py — Halaman Perbandingan Musim PaceFlow
# Berisi: multi-select season, championship progression, DNF trend,
#         WDC/WCC per season, gap tracker
# Update: Top N toggle (Top5/10/Semua) + pakai global btn_toggle dari components
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec, info_box, btn_toggle
from layout.design_tokens import C, F, rgba
from services.data_service import get_seasons


def layout():
    seasons = get_seasons()
    season_opts = [{"label": f"Musim {s}", "value": s} for s in seasons]

    return html.Div([
        sec("Perbandingan Musim", "lucide:git-compare"),
        info_box(
            "Pilih **2 hingga 3 musim** untuk membandingkan performa. "
            "Setiap musim ditampilkan dengan warna berbeda.",
            C["blue"]
        ),
        card(html.Div([
            html.Div("PILIH MUSIM (MAKS. 3)", style=dict(
                fontSize="9px", fontWeight="700", letterSpacing="1.5px",
                textTransform="uppercase", color=C["muted"],
                marginBottom="8px", fontFamily=F)),
            dcc.Dropdown(
                id="cmp-season-select",
                options=season_opts,
                value=[],
                multi=True,
                placeholder="Pilih musim...",
                style=dict(fontSize="12px"),
            ),
            html.Div(id="cmp-season-warning", style=dict(marginTop="8px")),
        ])),
        sec("Juara per Musim", "lucide:trophy"),
        html.Div(id="cmp-champions-row"),
        sec("Perkembangan Poin Pembalap", "lucide:line-chart"),
        card(html.Div([
            # Baris kontrol: Mode (Poin/Posisi) + Top N (Top 5/10/Semua)
            html.Div([
                html.Div([
                    btn_toggle("btn-cmp-poin",   "Poin Kumulatif",       True),
                    btn_toggle("btn-cmp-posisi", "Posisi Championship", False),
                ], style=dict(display="flex", gap="6px")),
                html.Div([
                    btn_toggle("btn-cmp-top5",   "Top 5",  True),
                    btn_toggle("btn-cmp-top10",  "Top 10", False),
                    btn_toggle("btn-cmp-topall", "Semua",  False),
                ], style=dict(display="flex", gap="6px")),
            ], style=dict(display="flex", justifyContent="space-between",
                          marginBottom="12px")),
            dcc.Graph(id="cmp-progression-chart", config=dict(displayModeBar=False)),
        ])),
        sec("Poin Konstruktor", "lucide:shield"),
        card(dcc.Graph(id="cmp-constructor-chart", config=dict(displayModeBar=False))),
        sec("Tren DNF per Musim", "lucide:circle-x"),
        card(dcc.Graph(id="cmp-dnf-chart", config=dict(displayModeBar=False))),
        sec("Gap Poin P1 vs P2 per Round", "lucide:trending-up"),
        card(dcc.Graph(id="cmp-gap-chart", config=dict(displayModeBar=False))),
        dcc.Store(id="store-cmp-mode",  data="poin"),
        dcc.Store(id="store-cmp-topn",  data=5),
    ])
