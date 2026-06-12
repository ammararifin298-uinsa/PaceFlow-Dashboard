# =============================================================================
# pages/comparison/callbacks.py — Callbacks Halaman Perbandingan Musim
# Update: Top N toggle (Top5/10/Semua) + klik legenda fokus (parse_restyle)
#         + pakai BTN_ACTIVE/BTN_INACTIVE global dari layout.components
# =============================================================================

from dash import Input, Output, State, no_update, callback_context
import plotly.graph_objects as go
import pandas as pd
from layout.design_tokens import C, CL, F, ax, legh, rgba, tc, MARKER_SYMBOLS
from layout.components import kpi_card, BTN_ACTIVE, BTN_INACTIVE
from dash import html
import dash_bootstrap_components as dbc

SEASON_COLORS = ["#1D4ED8", "#DC2626", "#059669"]

_XAXIS = dict(
    title_font=dict(size=11, color=C["muted"]),
    tickfont=dict(size=10, color=C["muted"]),
    gridcolor="#E2E8F0", linecolor=C["border"],
    zerolinecolor=C["border"],
)
_YAXIS = dict(
    title_font=dict(size=11, color=C["muted"]),
    tickfont=dict(size=10, color=C["muted"]),
    gridcolor="#E2E8F0", linecolor=C["border"],
    zerolinecolor=C["border"],
)


def register_callbacks(app):

    # Validasi warning saja (bukan rewrite value — hindari circular dependency)
    @app.callback(
        Output("cmp-season-warning", "children"),
        Input("cmp-season-select",   "value"),
        prevent_initial_call=True,
    )
    def validate_seasons(selected):
        if not selected:
            return html.Span()
        if len(selected) > 3:
            return html.Span("⚠ Maksimal 3 musim. Hanya 3 pertama ditampilkan.",
                style=dict(fontSize="11px", color=C["orange"], fontFamily=F))
        return html.Span()

    # ── Toggle Mode (Poin / Posisi) ────────────────────────────────────────────
    @app.callback(
        Output("store-cmp-mode",  "data"),
        Output("btn-cmp-poin",    "style"),
        Output("btn-cmp-posisi",  "style"),
        Input("btn-cmp-poin",     "n_clicks"),
        Input("btn-cmp-posisi",   "n_clicks"),
        State("store-cmp-mode",   "data"),
        prevent_initial_call=True,
    )
    def toggle_mode(n_poin, n_posisi, current):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if tid == "btn-cmp-poin":
            return "poin", BTN_ACTIVE, BTN_INACTIVE
        return "posisi", BTN_INACTIVE, BTN_ACTIVE

    # ── Toggle Top N ──────────────────────────────────────────────────────────
    @app.callback(
        Output("store-cmp-topn",   "data"),
        Output("btn-cmp-top5",     "style"),
        Output("btn-cmp-top10",    "style"),
        Output("btn-cmp-topall",   "style"),
        Input("btn-cmp-top5",      "n_clicks"),
        Input("btn-cmp-top10",     "n_clicks"),
        Input("btn-cmp-topall",    "n_clicks"),
        State("store-cmp-topn",    "data"),
        prevent_initial_call=True,
    )
    def toggle_topn(n5, n10, nall, current):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if tid == "btn-cmp-top5":
            return 5,   BTN_ACTIVE, BTN_INACTIVE, BTN_INACTIVE
        if tid == "btn-cmp-top10":
            return 10,  BTN_INACTIVE, BTN_ACTIVE, BTN_INACTIVE
        if tid == "btn-cmp-topall":
            return 999, BTN_INACTIVE, BTN_INACTIVE, BTN_ACTIVE
        return current, BTN_ACTIVE, BTN_INACTIVE, BTN_INACTIVE

    @app.callback(
        Output("cmp-champions-row", "children"),
        Input("cmp-season-select",  "value"),
    )
    def update_champions(selected):
        if not selected or len(selected) < 2:
            return html.Div("Pilih minimal 2 musim.",
                style=dict(fontSize="12px", color=C["muted"],
                           fontFamily=F, padding="8px"))
        from services.data_service import get_kpi
        cols = []
        for i, s in enumerate(selected[:3]):
            kp     = get_kpi(s)
            leader = str(kp.get("points_leader", "—"))
            lpts   = float(kp.get("leader_points", 0) or 0)
            lcon   = str(kp.get("leader_constructor", "—"))
            color  = SEASON_COLORS[i % len(SEASON_COLORS)]
            cols.append(dbc.Col(
                kpi_card(f"Musim {s}", leader,
                         f"{lpts:.0f} poin · {lcon}", color, "lucide:trophy"),
                width=4))
        return dbc.Row(cols, className="g-3")

    # ── Grafik Progres Championship ───────────────────────────────────────────────
    @app.callback(
        Output("cmp-progression-chart", "figure"),
        Input("cmp-season-select",       "value"),
        Input("store-cmp-mode",          "data"),
        Input("store-cmp-topn",          "data"),
    )
    def update_progression(selected, mode, top_n):
        if not selected or len(selected) < 2:
            return go.Figure()
        from services.data_service import get_analytics
        top_n = top_n or 5
        mode  = mode or "poin"
        fig   = go.Figure()

        for i, s in enumerate(selected[:3]):
            df = get_analytics(s)
            if df.empty:
                continue
            color = SEASON_COLORS[i % len(SEASON_COLORS)]
            tr = (df.groupby(["driver_name", "round", "race_name"],
                              as_index=False)["season_cumulative_points"].max()
                    .sort_values(["driver_name", "round"]))

            # Pilih top N berdasarkan poin max
            topN = (tr.groupby("driver_name")["season_cumulative_points"]
                    .max().nlargest(top_n if top_n < 999 else len(tr["driver_name"].unique()))
                    .index.tolist())
            top5_always = (tr.groupby("driver_name")["season_cumulative_points"]
                           .max().nlargest(5).index.tolist())

            for j, drv in enumerate(topN):
                d   = tr[tr["driver_name"] == drv].sort_values("round")
                grp = f"{drv} ({s})"

                hl  = drv in top5_always
                lw, ms, op = (2.5, 8, 1.0) if hl else (1.0, 4, 0.4)

                fig.add_trace(go.Scatter(
                    x=d["round"], y=d["season_cumulative_points"],
                    mode="lines+markers", name=grp,
                    visible=True, opacity=op,
                    line=dict(width=lw, color=color,
                              dash=["solid", "dash", "dot"][i % 3]),
                    marker=dict(size=ms, color=color,
                                symbol=MARKER_SYMBOLS[j % len(MARKER_SYMBOLS)]),
                    hovertemplate=(f"<b>{drv} ({s})</b><br>"
                                   f"R%{{x}}: %{{y}} poin<extra></extra>")
                ))

        fig.update_layout(
            **CL, height=420,
            legend=dict(
                orientation="h", y=-0.25, x=0,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=10, color=C["muted"])
            ),
            xaxis={**_XAXIS, "title_text": "Putaran", "dtick": 2},
            yaxis={**_YAXIS, "title_text": "Poin Kumulatif"},
            hovermode="closest",
            margin=dict(l=55, r=20, t=20, b=100)
        )
        return fig

    @app.callback(
        Output("cmp-constructor-chart", "figure"),
        Input("cmp-season-select",      "value"),
    )
    def update_constructor(selected):
        if not selected or len(selected) < 2:
            return go.Figure()
        from services.data_service import get_constructor_season
        fig = go.Figure()
        for i, s in enumerate(selected[:3]):
            dc    = get_constructor_season(s)
            if dc.empty:
                continue
            color = SEASON_COLORS[i % len(SEASON_COLORS)]
            dc_s  = dc.nlargest(5, "total_points")
            fig.add_trace(go.Bar(
                x=dc_s["constructor"],
                y=dc_s["total_points"],
                name=f"Musim {s}",
                marker_color=color,
                marker_line=dict(width=0),
                hovertemplate=(f"<b>%{{x}}</b> ({s})<br>"
                               f"Poin: <b>%{{y}}</b><extra></extra>")
            ))
        fig.update_layout(
            **CL, height=320,
            legend=dict(
                orientation="h", y=-0.25, x=0,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=10, color=C["muted"])
            ),
            barmode="group",
            xaxis={**_XAXIS, "title_text": "Konstruktor"},
            yaxis={**_YAXIS, "title_text": "Total Poin"},
            margin=dict(l=55, r=20, t=20, b=100)
        )
        return fig

    @app.callback(
        Output("cmp-dnf-chart",    "figure"),
        Input("cmp-season-select", "value"),
    )
    def update_dnf(selected):
        if not selected or len(selected) < 2:
            return go.Figure()
        from services.data_service import get_kpi
        seasons_list, dnf_rates, dnf_counts = [], [], []
        for s in selected[:3]:
            kp   = get_kpi(s)
            dnf  = int(kp.get("total_dnf", 0) or 0)
            tot  = int(kp.get("total_entries", 1) or 1)
            rate = round(dnf / tot * 100, 1) if tot > 0 else 0
            seasons_list.append(f"Musim {s}")
            dnf_rates.append(rate)
            dnf_counts.append(dnf)

        fig = go.Figure(go.Bar(
            x=seasons_list, y=dnf_rates,
            marker_color=[SEASON_COLORS[i] for i in range(len(seasons_list))],
            marker_line=dict(width=0),
            text=[f"{r}%\n({c} DNF)" for r, c in zip(dnf_rates, dnf_counts)],
            textposition="outside",
            textfont=dict(size=10, color=C["muted"]),
            hovertemplate="<b>%{x}</b><br>DNF Rate: <b>%{y}%</b><extra></extra>",
            showlegend=False,
        ))
        fig.update_layout(
            **CL, height=280,
            xaxis={**_XAXIS, "title_text": "Musim"},
            yaxis={**_YAXIS, "title_text": "DNF Rate (%)"},
            margin=dict(l=55, r=20, t=20, b=40)
        )
        return fig

    @app.callback(
        Output("cmp-gap-chart",    "figure"),
        Input("cmp-season-select", "value"),
    )
    def update_gap(selected):
        if not selected or len(selected) < 2:
            return go.Figure()
        from services.data_service import get_analytics
        fig = go.Figure()
        for i, s in enumerate(selected[:3]):
            df = get_analytics(s)
            if df.empty:
                continue
            color  = SEASON_COLORS[i % len(SEASON_COLORS)]
            rounds = sorted(df["round"].unique())
            gaps   = []
            for r in rounds:
                snap = (df[df["round"] == r]
                        .sort_values("season_cumulative_points", ascending=False)
                        .drop_duplicates("driver_id"))
                if len(snap) >= 2:
                    p1 = float(snap.iloc[0]["season_cumulative_points"])
                    p2 = float(snap.iloc[1]["season_cumulative_points"])
                    gaps.append(p1 - p2)
                else:
                    gaps.append(0)

            fig.add_trace(go.Scatter(
                x=rounds, y=gaps,
                mode="lines+markers", name=f"Musim {s}",
                line=dict(width=2, color=color,
                          dash=["solid", "dash", "dot"][i % 3]),
                marker=dict(size=6, color=color),
                hovertemplate=(f"<b>Musim {s}</b><br>"
                               f"R%{{x}}: Gap <b>%{{y:.0f}} poin</b>"
                               f"<extra></extra>")
            ))

        fig.update_layout(
            **CL, height=300, legend=_LEGEND,
            xaxis={**_XAXIS, "title_text": "Putaran", "dtick": 2},
            yaxis={**_YAXIS, "title_text": "Gap Poin P1 vs P2"},
            hovermode="closest",
            margin=dict(l=55, r=20, t=20, b=100)
        )
        return fig

