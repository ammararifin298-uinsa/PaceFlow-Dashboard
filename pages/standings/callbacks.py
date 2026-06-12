from dash import Input, Output, State, no_update, callback_context
import plotly.graph_objects as go
import pandas as pd
from layout.design_tokens import C, tc, CL, ax
from services.data_service import get_constructor_progression

def register_callbacks(app):

    # ── Toggle Top N constructor prog chart ──────────────────────────────────────
    @app.callback(
        Output("store-stnd-con-topn", "data"),
        Input("btn-stnd-con-top5",  "n_clicks"),
        Input("btn-stnd-con-top10", "n_clicks"),
        Input("btn-stnd-con-topall","n_clicks"),
        State("store-stnd-con-topn", "data"),
        prevent_initial_call=True,
    )
    def update_con_topn(n5, n10, nall, current):
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        tid = ctx.triggered[0]["prop_id"].split(".")[0]
        if tid == "btn-stnd-con-top5":   return 5
        if tid == "btn-stnd-con-top10":  return 10
        if tid == "btn-stnd-con-topall": return 999
        return current

    # ── Style tombol con prog ──────────────────────────────────────────────────
    @app.callback(
        Output("btn-stnd-con-top5",  "style"),
        Output("btn-stnd-con-top10", "style"),
        Output("btn-stnd-con-topall","style"),
        Input("store-stnd-con-topn", "data"),
    )
    def update_con_btn_styles(top_n):
        from layout.components import BTN_ACTIVE, BTN_INACTIVE
        return (
            BTN_ACTIVE if top_n == 5 else BTN_INACTIVE,
            BTN_ACTIVE if top_n == 10 else BTN_INACTIVE,
            BTN_ACTIVE if top_n >= 999 else BTN_INACTIVE,
        )

    # ── Rebuild Constructor Progression Figure ──────────────────────────────
    @app.callback(
        Output("graph-stnd-con-prog", "figure"),
        Input("store-stnd-con-prog-data", "data"), # Triggered by season change (data=season)
        Input("store-stnd-con-topn", "data"),
        Input("graph-stnd-con-prog", "restyleData"),
        State("graph-stnd-con-prog", "figure")
    )
    def render_con_prog_chart(season, top_n, restyle_data, current_fig):
        if not season:
            return no_update

        # Deteksi legend click
        selected_team = None
        if restyle_data and current_fig and "data" in current_fig:
            from layout.graph_utils import parse_restyle
            # Fix M-9: was passing current_fig (dict), should be current_fig["data"] (list)
            clicked_name = parse_restyle(restyle_data, current_fig["data"])
            if clicked_name:
                selected_team = clicked_name

        prog_df = get_constructor_progression(season)
        fig_prog = go.Figure()
        if prog_df.empty:
            return fig_prog

        teams = prog_df["constructor"].unique().tolist()
        top_teams = (prog_df.groupby("constructor")["cumulative_points"]
                     .max().nlargest(top_n).index.tolist())
        top3 = (prog_df.groupby("constructor")["cumulative_points"]
                     .max().nlargest(3).index.tolist())
        is_all = top_n >= 999

        for con in teams:
            sub = prog_df[prog_df["constructor"] == con].sort_values("round")
            color = tc(con)

            if is_all:
                if selected_team is not None:
                    if con == selected_team:
                        lw, ms, op, vis = 2.5, 8, 1.0, True
                    else:
                        lw, ms, op, vis = 1.0, 4, 0.15, "legendonly"
                else:
                    hl = con in top3
                    lw, ms, op, vis = (2.5, 7, 1.0, True) if hl else (1.0, 4, 0.2, True)
            else:
                if con not in top_teams:
                    continue
                if selected_team is not None:
                    if con == selected_team:
                        lw, ms, op, vis = 2.5, 8, 1.0, True
                    else:
                        lw, ms, op, vis = 1.0, 4, 0.15, "legendonly"
                else:
                    lw, ms, op, vis = 2.5, 7, 1.0, True

            # Dummy trace for legend
            fig_prog.add_trace(go.Scatter(
                x=[None], y=[None],
                mode="lines+markers", name=con,
                legendgroup=con, showlegend=True,
                visible=True if (selected_team is None or con == selected_team) else "legendonly",
                hoverinfo="skip",
                line=dict(width=2.5, color=color),
                marker=dict(size=7, color="#FFFFFF", line=dict(width=2, color=color))
            ))
            # Actual trace
            fig_prog.add_trace(go.Scatter(
                x=sub["round"],
                y=sub["cumulative_points"],
                mode="lines+markers",
                name=con,
                legendgroup=con, showlegend=False,
                visible=vis, opacity=op,
                line=dict(color=color, width=lw),
                marker=dict(size=ms, color="#FFFFFF", line=dict(width=2, color=color)),
                hovertemplate=(f"<b>{con}</b><br>Round %{{x}}<br>"
                               "Poin: <b>%{y:.0f}</b><extra></extra>")
            ))

        fig_prog.update_layout(
            **CL, height=320,
            xaxis=ax("Round", dtick=1),
            yaxis=ax("Poin Kumulatif"),
            legend=dict(
                orientation="h", y=-0.25, x=0,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=9, color=C["muted"]),
                itemsizing="constant",
                itemclick="toggleothers",
                itemdoubleclick="toggle",
            ),
            margin=dict(l=40, r=20, t=10, b=60),
            hovermode="x unified",
        )
        return fig_prog
