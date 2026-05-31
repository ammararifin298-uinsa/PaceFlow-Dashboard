# =============================================================================
# pages/h2h/callbacks.py — Callbacks untuk halaman H2H PaceFlow
# Berisi: update radar chart, bar chart, tabel perbandingan
# Fix: tiap driver bisa dari season berbeda (lintas musim)
# Metrik normalized: win rate %, podium rate %, avg points per race
# =============================================================================

from dash import Input, Output, State, callback_context, no_update
import plotly.graph_objects as go
from dash import html
from layout.components import tbl_hdr, safe_col
from layout.design_tokens import C, F, CL, ax, rgba, tc
from services.data_service import get_analytics


METRICS = ["Avg Poin/Race", "Win Rate %", "Podium Rate %", "Pole Rate %", "FL Rate %", "DNF Rate %"]
DRIVER_COLORS = [C["red"], C["blue"], C["orange"]]


def _get_driver_stats(driver_name: str, season: int) -> dict | None:
    """Ambil statistik normalized per driver per season."""
    df = get_analytics(season)
    if df.empty:
        return None

    d = df[df["driver_name"] == driver_name]
    if d.empty:
        return None

    total = len(d)
    wins  = int(d["is_win"].sum())
    pods  = int(d["is_podium"].sum())
    poles = int((d["qualifying_pos"] == 1).sum()) if safe_col(d, "qualifying_pos") else 0
    fl    = int((d["fastest_lap_rank"] == 1).sum()) if safe_col(d, "fastest_lap_rank") else 0
    dnf   = int(d["is_dnf"].sum()) if safe_col(d, "is_dnf") else 0
    pts   = float(d["race_points"].sum()) if safe_col(d, "race_points") else 0

    return {
        "driver":   driver_name,
        "season":   season,
        "total":    total,
        "avg_pts":  round(pts / total, 2) if total > 0 else 0,
        "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
        "pod_rate": round(pods / total * 100, 1) if total > 0 else 0,
        "pole_rate":round(poles / total * 100, 1) if total > 0 else 0,
        "fl_rate":  round(fl / total * 100, 1) if total > 0 else 0,
        "dnf_rate": round(dnf / total * 100, 1) if total > 0 else 0,
        "wins":     wins,
        "pods":     pods,
        "poles":    poles,
        "fl":       fl,
        "dnf":      dnf,
        "pts_total":round(pts, 1),
    }


def register_callbacks(app):
    @app.callback(
        Output("h2h-radar",  "figure"),
        Output("h2h-bar",    "figure"),
        Output("h2h-table",  "children"),
        Input("h2h-d1", "value"), Input("h2h-s1", "value"),
        Input("h2h-d2", "value"), Input("h2h-s2", "value"),
        Input("h2h-d3", "value"), Input("h2h-s3", "value"),
        prevent_initial_call=False,
    )
    def h2h_update(d1, s1, d2, s2, d3, s3):
        pairs = [(d, s) for d, s in [(d1,s1),(d2,s2),(d3,s3)] if d and s]
        em    = go.Figure()
        em.update_layout(**CL, height=300,
                         xaxis=ax(), yaxis=ax(),
                         margin=dict(l=40, r=20, t=20, b=40))

        if len(pairs) < 2:
            msg = html.Div([
                ico_("lucide:users", 36, C["border"]),
                html.Div("Pilih minimal 2 pembalap untuk membandingkan",
                    style=dict(color=C["muted"], fontSize="13px",
                               fontFamily=F, marginTop="12px")),
            ], style=dict(display="flex", flexDirection="column",
                          alignItems="center", justifyContent="center",
                          padding="40px", textAlign="center"))
            return em, em, msg

        stats = []
        for drv, ssn in pairs:
            s = _get_driver_stats(drv, ssn)
            if s:
                stats.append(s)

        if len(stats) < 2:
            return em, em, html.Div("Data tidak tersedia untuk pembalap yang dipilih.",
                style=dict(color=C["muted"], fontSize="13px", fontFamily=F, padding="20px"))

        # Radar chart
        rf = go.Figure()
        for i, s in enumerate(stats):
            color = DRIVER_COLORS[i % len(DRIVER_COLORS)]
            vals  = [s["avg_pts"], s["win_rate"], s["pod_rate"],
                     s["pole_rate"], s["fl_rate"],
                     max(0, 100 - s["dnf_rate"])]  # DNF diinvert
            rf.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=METRICS + [METRICS[0]],
                fill="toself", name=f"{s['driver']} ({s['season']})",
                line_color=color, fillcolor=rgba(color, 0.15)
            ))
        rf.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, gridcolor=C["border"],
                                tickfont=dict(size=8, color=C["muted"])),
                angularaxis=dict(tickfont=dict(size=10, color=C["text"], family=F)),
                bgcolor=C["surface"]
            ),
            paper_bgcolor=C["surface"],
            font=dict(family=F, color=C["text"], size=11),
            legend=dict(orientation="h", y=-0.15, bgcolor="rgba(0,0,0,0)",
                        font=dict(size=10, color=C["text"])),
            height=320, margin=dict(l=20, r=20, t=20, b=60)
        )

        # Bar chart
        bf = go.Figure()
        bar_metrics = ["avg_pts", "win_rate", "pod_rate", "pole_rate", "fl_rate", "dnf_rate"]
        bar_labels  = ["Avg Poin", "Win %", "Podium %", "Pole %", "FL %", "DNF %"]
        for i, s in enumerate(stats):
            color = DRIVER_COLORS[i % len(DRIVER_COLORS)]
            bf.add_trace(go.Bar(
                name=f"{s['driver']} ({s['season']})",
                x=bar_labels,
                y=[s[m] for m in bar_metrics],
                marker_color=color, marker_line=dict(width=0),
                hovertemplate=f"<b>{s['driver']}</b><br>%{{x}}: %{{y}}<extra></extra>"
            ))
        bf.update_layout(**CL, height=320, barmode="group",
            legend=dict(orientation="h", y=1.06, bgcolor="rgba(0,0,0,0)",
                        font=dict(size=10, color=C["text"])),
            xaxis=ax(), yaxis=ax("Nilai"),
            margin=dict(l=40, r=20, t=20, b=40))

        # Tabel perbandingan
        rows = []
        for i, s in enumerate(stats):
            color = DRIVER_COLORS[i % len(DRIVER_COLORS)]
            rows.append(html.Tr([
                html.Td(f"{s['driver']} ({s['season']})",
                    style=dict(color=color, fontSize="12px", fontWeight="700",
                               padding="10px 12px", fontFamily=F)),
                html.Td(f"{s['pts_total']:.0f}",
                    style=dict(color=C["text"], fontSize="12px",
                               textAlign="center", padding="10px 10px", fontFamily=F)),
                html.Td(f"{s['avg_pts']:.1f}",
                    style=dict(color=C["blue"], fontSize="12px",
                               textAlign="center", padding="10px 8px", fontFamily=F)),
                html.Td(f"{s['win_rate']:.1f}%",
                    style=dict(color=C["orange"], fontWeight="700",
                               fontSize="12px", textAlign="center",
                               padding="10px 8px", fontFamily=F)),
                html.Td(f"{s['pod_rate']:.1f}%",
                    style=dict(color=C["teal"], fontWeight="600",
                               fontSize="12px", textAlign="center",
                               padding="10px 8px", fontFamily=F)),
                html.Td(f"{s['dnf_rate']:.1f}%",
                    style=dict(color=C["red"], fontWeight="600",
                               fontSize="12px", textAlign="center",
                               padding="10px 8px", fontFamily=F)),
            ], style=dict(borderBottom=f"1px solid {C['border']}")))

        tbl = html.Div([
            html.Div("Perbandingan Statistik Normalized",
                style=dict(fontSize="11px", fontWeight="600",
                           color=C["muted"], marginBottom="10px", fontFamily=F)),
            html.Table([
                tbl_hdr("Pembalap", "Total Poin", "Avg/Race", "Win %", "Podium %", "DNF %"),
                html.Tbody(rows),
            ], style=dict(width="100%", borderCollapse="collapse")),
        ])

        return rf, bf, tbl


def ico_(name, size=16, color=None):
    from dash_iconify import DashIconify
    return DashIconify(icon=name, width=size, height=size, color=color or C["muted"])