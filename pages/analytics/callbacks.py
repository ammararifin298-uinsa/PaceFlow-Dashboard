# =============================================================================
# pages/analytics/callbacks.py — Callbacks interaktif Halaman Analitik
# Berisi: toggle Top N speed chart + highlight tim via klik legend
# Pattern: konsisten dengan home/callbacks.py (dummy trace + single-stage callbacks)
# =============================================================================

from dash import Input, Output, State, no_update, callback_context
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from layout.design_tokens import C, CL, tc, MARKER_SYMBOLS

F = "Inter, -apple-system, sans-serif"

BTN_ACTIVE   = dict(background=C["blue"], color="#FFF",
                    border=f"1px solid {C['blue']}", borderRadius="6px",
                    padding="4px 14px", fontSize="11px", fontWeight="600",
                    fontFamily=F, cursor="pointer")
BTN_INACTIVE = dict(background=C["surface"], color=C["muted"],
                    border=f"1px solid {C['border']}", borderRadius="6px",
                    padding="4px 14px", fontSize="11px", fontWeight="600",
                    fontFamily=F, cursor="pointer")

_LEGEND = dict(
    orientation="v", x=1.02, y=1,
    xanchor="left", yanchor="top",
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=8, color=C["muted"]),
    itemsizing="constant",
    itemclick="toggleothers",
    itemdoubleclick="toggle",
)
_XAXIS = dict(
    title_font=dict(size=11, color=C["muted"]),
    tickfont=dict(size=10, color=C["muted"]),
    gridcolor="#E2E8F0", gridwidth=1,
    linecolor=C["border"], zerolinecolor="#CBD5E1", zerolinewidth=1,
    showgrid=True,
)
_YAXIS = dict(
    title_font=dict(size=11, color=C["muted"]),
    tickfont=dict(size=10, color=C["muted"]),
    gridcolor="#E2E8F0", gridwidth=1,
    linecolor=C["border"], zerolinecolor="#CBD5E1", zerolinewidth=1,
    showgrid=True,
)


def _parse_restyle(restyle_data, traces):
    try:
        style_updates = restyle_data[0]
        trace_indices = restyle_data[1]
        visibilities  = style_updates.get("visible", [])
        if not visibilities:
            return None

        # Kasus 1: deteksi grup legenda mana saja yang diaktifkan (True)
        if not isinstance(visibilities, list):
            visibilities = [visibilities]

        apply_single_val = (len(visibilities) == 1)
        trues = set()

        for j, idx in enumerate(trace_indices):
            vis = visibilities[0] if apply_single_val else (visibilities[j] if j < len(visibilities) else None)
            if idx < len(traces):
                grp = traces[idx].get("legendgroup")
                if grp and vis is True:
                    trues.add(grp)

        # Jika ada lebih dari satu grup diubah menjadi True -> reset/show-all
        if len(trues) > 1:
            return None

        # Jika hanya ada tepat satu grup diubah menjadi True -> isolasi grup tersebut
        if len(trues) == 1:
            return list(trues)[0]

        # Kasus 2: semua menjadi legendonly → temukan driver/tim aktif berdasarkan exclusion
        is_all_legendonly = False
        if apply_single_val and visibilities[0] == "legendonly":
            is_all_legendonly = True
        elif not apply_single_val and all(v == "legendonly" for v in visibilities):
            is_all_legendonly = True

        if is_all_legendonly:
            hidden_set = set(trace_indices)
            for i, trace in enumerate(traces):
                if i not in hidden_set:
                    grp   = trace.get("legendgroup")
                    x_val = trace.get("x")
                    if grp and x_val is not None and x_val != [None]:
                        return grp
        return None
    except Exception:
        return None


def _build_speed_fig(sg, top_n=5, selected_team=None):
    if sg.empty:
        return go.Figure()

    teams    = list(sg["constructor"].unique())
    top_n_teams = (sg.groupby("constructor")["avg_speed_kph"]
                   .mean().nlargest(top_n).index.tolist())
    top3     = (sg.groupby("constructor")["avg_speed_kph"]
                .mean().nlargest(3).index.tolist())
    is_all   = top_n >= 999
    fig      = go.Figure()

    for i, team in enumerate(teams):
        d     = sg[sg["constructor"] == team].sort_values("round")
        color = tc(team)
        sym   = MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)]

        if is_all:
            if selected_team is not None:
                if team == selected_team:
                    lw, ms, op, vis = 2.5, 8, 1.0, True
                else:
                    lw, ms, op, vis = 1.0, 4, 0.15, "legendonly"
            else:
                hl = team in top3
                lw, ms, op, vis = (2.5, 7, 1.0, True) if hl else (1.0, 4, 0.2, True)
        else:
            if team not in top_n_teams:
                continue
            if selected_team is not None:
                if team == selected_team:
                    lw, ms, op, vis = 2.5, 8, 1.0, True
                else:
                    lw, ms, op, vis = 1.0, 4, 0.15, "legendonly"
            else:
                lw, ms, op, vis = 2.5, 7, 1.0, True

        # Dummy trace
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines+markers", name=team,
            legendgroup=team, showlegend=True,
            visible=True if (selected_team is None or team == selected_team) else "legendonly",
            hoverinfo="skip",
            line=dict(width=2.5, color=color),
            marker=dict(size=7, color="#FFFFFF", symbol=sym,
                        line=dict(width=2, color=color))
        ))
        # Trace aktual
        fig.add_trace(go.Scatter(
            x=d["round"].tolist(), y=d["avg_speed_kph"].tolist(),
            mode="lines+markers", name=team,
            legendgroup=team, showlegend=False,
            visible=vis, opacity=op,
            line=dict(width=lw, color=color),
            marker=dict(size=ms, color="#FFFFFF", symbol=sym,
                        line=dict(width=2, color=color)),
            customdata=d["race_name"].tolist(),
            hovertemplate=(f"<b>{team}</b><br>%{{customdata}}<br>"
                           f"Kecepatan: <b>%{{y:.1f}} km/h</b><extra></extra>")
        ))

    max_round = int(sg["round"].max()) if not sg.empty else 1
    fig.update_layout(
        **CL, height=360, legend=_LEGEND,
        xaxis={**_XAXIS, "title_text": "Putaran", "dtick": 2,
               "range": [0.5, max_round + 0.5]},
        yaxis={**_YAXIS, "title_text": "Kecepatan Rata-rata (km/h)"},
        hovermode="closest",
        margin=dict(l=65, r=100, t=10, b=40)
    )
    return fig


def _build_qualifying_fig(qvr, top_n=5, selected_team=None):
    if qvr.empty:
        return go.Figure()

    rng   = np.random.default_rng(42)
    teams = list(qvr["constructor"].unique())
    top_n_teams = (qvr.groupby("constructor").size().nlargest(top_n).index.tolist())
    is_all = top_n >= 999
    top5  = (qvr.groupby("constructor").size().nlargest(5).index.tolist())
    fig   = go.Figure()

    for i, team in enumerate(teams):
        if not is_all and team not in top_n_teams:
            continue
        d     = qvr[qvr["constructor"] == team]
        color = tc(team)
        sym   = MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)]
        n     = len(d)
        jx    = rng.uniform(-0.25, 0.25, n)
        jy    = rng.uniform(-0.25, 0.25, n)
        x_jit = [float(p) + float(jx[k]) for k, p in enumerate(d["qualifying_pos"].tolist())]
        y_jit = [float(p) + float(jy[k]) for k, p in enumerate(d["position"].tolist())]

        if selected_team is not None:
            if team == selected_team:
                ms, op, vis = 10, 1.0, True
            else:
                ms, op, vis = 6, 0.15, "legendonly"
        else:
            hl = team in top_n_teams if not is_all else team in top5
            ms, op, vis = (9, 0.75, True) if hl else (6, 0.2, True)

        # Dummy trace
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers", name=team,
            legendgroup=team, showlegend=True,
            visible=True if (selected_team is None or team == selected_team) else "legendonly",
            hoverinfo="skip",
            marker=dict(size=9, color=color, symbol="circle",
                        line=dict(width=1, color="#FFFFFF"))
        ))
        # Trace aktual dengan jitter
        fig.add_trace(go.Scatter(
            x=x_jit, y=y_jit,
            mode="markers", name=team,
            legendgroup=team, showlegend=False,
            visible=vis, opacity=op,
            marker=dict(size=ms, color=color, symbol="circle",
                        line=dict(width=1, color="#FFFFFF")),
            customdata=d[["driver_name", "race_name",
                          "qualifying_pos", "position"]].values.tolist(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                "Kualifikasi: <b>P%{customdata[2]:.0f}</b> → "
                "Finish: <b>P%{customdata[3]:.0f}</b>"
                "<extra></extra>"
            )
        ))

    mp = int(qvr[["qualifying_pos", "position"]].max().max())
    fig.add_shape(type="line", x0=1, y0=1, x1=mp, y1=mp,
        layer="below", line=dict(color=C["red"], dash="dot", width=1))
    fig.add_annotation(
        x=mp * 0.22, y=mp * 0.78, text="▲ Gain Posisi", showarrow=False,
        font=dict(color=C["green"], size=10, family=F),
        bgcolor="rgba(5,150,105,0.08)", bordercolor="rgba(5,150,105,0.3)",
        borderpad=4, borderwidth=1)
    fig.add_annotation(
        x=mp * 0.78, y=mp * 0.22, text="▼ Kehilangan Posisi", showarrow=False,
        font=dict(color=C["red"], size=10, family=F),
        bgcolor="rgba(220,38,38,0.08)", bordercolor="rgba(220,38,38,0.3)",
        borderpad=4, borderwidth=1)
    fig.update_layout(
        **CL, height=360, legend=_LEGEND,
        xaxis={**_XAXIS, "title_text": "Posisi Kualifikasi (Grid)", "dtick": 2},
        yaxis={**_YAXIS, "title_text": "Posisi Finish", "dtick": 2,
               "autorange": "reversed"},
        hovermode="closest",
        margin=dict(l=55, r=100, t=10, b=40)
    )
    return fig


def register_callbacks(app):

    # ── Toggle Top N speed chart ──────────────────────────────────────────────
    @app.callback(
        Output("store-spd-topn", "data"),
        Input("btn-spd-top5",  "n_clicks"),
        Input("btn-spd-top10", "n_clicks"),
        Input("btn-spd-topall","n_clicks"),
        State("store-spd-topn", "data"),
        prevent_initial_call=True,
    )
    def update_spd_topn(n5, n10, nall, current):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if tid == "btn-spd-top5":   return 5
        if tid == "btn-spd-top10":  return 10
        if tid == "btn-spd-topall": return 999
        return current

    # ── Style tombol speed ────────────────────────────────────────────────────
    @app.callback(
        Output("btn-spd-top5",  "style"),
        Output("btn-spd-top10", "style"),
        Output("btn-spd-topall","style"),
        Input("store-spd-topn", "data"),
    )
    def update_spd_btn_styles(top_n):
        top_n = top_n or 5
        return (BTN_ACTIVE if top_n == 5   else BTN_INACTIVE,
                BTN_ACTIVE if top_n == 10  else BTN_INACTIVE,
                BTN_ACTIVE if top_n == 999 else BTN_INACTIVE)

    # ── Single-stage rebuild speed figure & legend click ──────────────────────
    @app.callback(
        Output("graph-analitik-spd", "figure"),
        Input("store-analitik-data", "data"),
        Input("store-spd-topn",      "data"),
        Input("graph-analitik-spd",  "restyleData"),
        State("graph-analitik-spd",  "figure"),
    )
    def update_speed(data, top_n, restyle_data, current_fig):
        if not data:
            return go.Figure()
        df  = pd.DataFrame(data)
        sg  = (df.dropna(subset=["avg_speed_kph"])
                 .groupby(["constructor", "race_name", "round"])["avg_speed_kph"]
                 .mean().reset_index().sort_values("round"))
        if sg.empty or float(sg["avg_speed_kph"].sum()) == 0:
            return go.Figure()

        top_n = top_n or 5
        ctx = callback_context
        triggered_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        selected_team = None

        if "restyleData" in triggered_id and restyle_data and current_fig:
            selected_team = _parse_restyle(restyle_data, current_fig["data"])

        return _build_speed_fig(sg, top_n, selected_team)

    # ── Toggle Top N qualifying chart ─────────────────────────────────────────
    @app.callback(
        Output("store-qvr-topn", "data"),
        Input("btn-qvr-top5",  "n_clicks"),
        Input("btn-qvr-top10", "n_clicks"),
        Input("btn-qvr-topall","n_clicks"),
        State("store-qvr-topn", "data"),
        prevent_initial_call=True,
    )
    def update_qvr_topn(n5, n10, nall, current):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if tid == "btn-qvr-top5":   return 5
        if tid == "btn-qvr-top10":  return 10
        if tid == "btn-qvr-topall": return 999
        return current

    # ── Style tombol qualifying ───────────────────────────────────────────────
    @app.callback(
        Output("btn-qvr-top5",  "style"),
        Output("btn-qvr-top10", "style"),
        Output("btn-qvr-topall","style"),
        Input("store-qvr-topn", "data"),
    )
    def update_qvr_btn_styles(top_n):
        top_n = top_n or 5
        return (BTN_ACTIVE if top_n == 5   else BTN_INACTIVE,
                BTN_ACTIVE if top_n == 10  else BTN_INACTIVE,
                BTN_ACTIVE if top_n == 999 else BTN_INACTIVE)

    # ── Single-stage rebuild qualifying figure & legend click ─────────────────
    @app.callback(
        Output("graph-analitik-qvr", "figure"),
        Input("store-analitik-data", "data"),
        Input("store-qvr-topn",      "data"),
        Input("graph-analitik-qvr",  "restyleData"),
        State("graph-analitik-qvr",  "figure"),
    )
    def update_qualifying(data, top_n, restyle_data, current_fig):
        if not data:
            return go.Figure()
        df  = pd.DataFrame(data)
        qvr = df[["driver_name", "constructor", "qualifying_pos",
                   "position", "race_name"]].dropna(
                       subset=["qualifying_pos", "position"])
        if qvr.empty:
            return go.Figure()

        top_n = top_n or 5
        ctx = callback_context
        triggered_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        selected_team = None

        if "restyleData" in triggered_id and restyle_data and current_fig:
            selected_team = _parse_restyle(restyle_data, current_fig["data"])

        return _build_qualifying_fig(qvr, top_n, selected_team)