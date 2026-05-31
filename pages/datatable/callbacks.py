# =============================================================================
# pages/datatable/callbacks.py — Callbacks untuk halaman Tabel Data
# Berisi: switch tab, switch year filter
# =============================================================================

from dash import Input, Output, no_update


def register_callbacks(app):

    @app.callback(
        Output("tabel-drv", "style"),
        Output("tabel-con", "style"),
        Output("tabel-cal", "style"),
        Input("tabel-tabs", "value"),
        prevent_initial_call=True,
    )
    def switch_tab(tab):
        show = dict(display="block")
        hide = dict(display="none")
        if tab == "drv": return show, hide, hide
        if tab == "con": return hide, show, hide
        return hide, hide, show