# =============================================================================
# pages/comparison/layout.py — Halaman Perbandingan Musim PaceFlow
# Berisi: multi-select season, championship progression, DNF trend,
#         WDC/WCC per season, gap tracker
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec, info_box
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
                value=seasons[:2] if len(seasons) >= 2 else seasons,
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
            html.Div([
                html.Button("Poin Kumulatif", id="btn-cmp-poin", n_clicks=0,
                    style=dict(background=C["blue"], color="#FFF",
                               border=f"1px solid {C['blue']}", borderRadius="6px",
                               padding="4px 14px", fontSize="11px", fontWeight="600",
                               fontFamily=F, cursor="pointer")),
                html.Button("Posisi Championship", id="btn-cmp-posisi", n_clicks=0,
                    style=dict(background=C["surface"], color=C["muted"],
                               border=f"1px solid {C['border']}", borderRadius="6px",
                               padding="4px 14px", fontSize="11px", fontWeight="600",
                               fontFamily=F, cursor="pointer")),
            ], style=dict(display="flex", gap="6px", marginBottom="12px")),
            dcc.Graph(id="cmp-progression-chart", config=dict(displayModeBar=False)),
        ])),
        sec("Poin Konstruktor", "lucide:shield"),
        card(dcc.Graph(id="cmp-constructor-chart", config=dict(displayModeBar=False))),
        sec("Tren DNF per Musim", "lucide:circle-x"),
        card(dcc.Graph(id="cmp-dnf-chart", config=dict(displayModeBar=False))),
        sec("Gap Poin P1 vs P2 per Round", "lucide:trending-up"),
        card(dcc.Graph(id="cmp-gap-chart", config=dict(displayModeBar=False))),
        dcc.Store(id="store-cmp-mode", data="poin"),
    ])
