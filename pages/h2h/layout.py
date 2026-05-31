# =============================================================================
# pages/h2h/layout.py — Halaman Head-to-Head PaceFlow
# Berisi: perbandingan hingga 3 driver dengan filter season per driver
# Fix: tiap driver bisa pilih season berbeda (lintas musim)
# Callback ada di pages/h2h/callbacks.py
# =============================================================================

from dash import html, dcc
import dash_bootstrap_components as dbc
from layout.components import ico, card, sec, info_box
from layout.design_tokens import C, F
from services.data_service import get_analytics, get_seasons


def layout(season: int):
    """
    Layout H2H — season parameter dipakai sebagai default season dropdown.
    Tiap driver punya dropdown season sendiri (lintas musim supported).
    """
    seasons  = get_seasons()
    df       = get_analytics(season)
    drivers  = sorted(df["driver_name"].dropna().unique().tolist()) if not df.empty else []

    season_opts = [{"label": f"Musim {s}", "value": s} for s in seasons]
    driver_opts = [{"label": d, "value": d} for d in drivers]

    def driver_col(num, label, optional=False):
        """Helper buat kolom driver + season selector."""
        return dbc.Col([
            html.Div(label, style=dict(
                fontSize="10px", fontWeight="700", letterSpacing="1px",
                textTransform="uppercase", color=C["muted"],
                marginBottom="5px", fontFamily=F
            )),
            dcc.Dropdown(
                id=f"h2h-d{num}",
                options=driver_opts,
                value=None,
                placeholder="Pilih pembalap..." if not optional else "Opsional...",
                clearable=True,
                style=dict(fontSize="12px", marginBottom="6px")
            ),
            dcc.Dropdown(
                id=f"h2h-s{num}",
                options=season_opts,
                value=season,
                clearable=False,
                searchable=False,
                placeholder="Pilih musim...",
                style=dict(fontSize="11px")
            ),
        ], width=4)

    return html.Div([
        sec("Perbandingan Head-to-Head", "lucide:users"),
        info_box(
            "Pilih minimal 2 pembalap untuk membandingkan performa. "
            "Setiap pembalap bisa dipilih dari musim yang berbeda."
        ),
        card(dbc.Row([
            driver_col(1, "Pembalap 1"),
            driver_col(2, "Pembalap 2"),
            driver_col(3, "Pembalap 3 (Opsional)", optional=True),
        ], className="g-3"), p="16px"),

        dbc.Row([
            dbc.Col(card(dcc.Graph(id="h2h-radar",
                config=dict(displayModeBar=False))), width=6),
            dbc.Col(card(dcc.Graph(id="h2h-bar",
                config=dict(displayModeBar=False))), width=6),
        ], className="g-3"),

        card(html.Div(id="h2h-table")),
    ])