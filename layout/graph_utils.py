# =============================================================================
# layout/graph_utils.py — Utilitas grafik terpusat PaceFlow
# Berisi: _parse_restyle() untuk klik legenda "Klik 1x Fokus, Klik lagi Reset"
# Diimpor oleh: pages/home/callbacks.py, pages/analytics/callbacks.py,
#               pages/comparison/callbacks.py
# Satu implementasi = konsistensi interaksi di seluruh halaman.
# =============================================================================


def parse_restyle(restyle_data, traces):
    """
    Parse restyleData dari event klik legend Plotly.

    Perilaku yang diimplementasikan:
    - Klik 1x pada nama di legenda → isolasi/fokus pada 1 item itu
    - Klik lagi pada item yang sudah di-fokus → reset, tampilkan semua kembali

    Args:
        restyle_data: Output dari prop "restyleData" pada dcc.Graph
        traces: List trace dari current_fig["data"]

    Returns:
        str | None — nama legendgroup yang dipilih, atau None jika reset/show-all
    """
    try:
        style_updates = restyle_data[0]
        trace_indices = restyle_data[1]
        visibilities  = style_updates.get("visible", [])
        if not visibilities:
            return None

        if not isinstance(visibilities, list):
            visibilities = [visibilities]

        apply_single_val = (len(visibilities) == 1)
        trues = set()

        for j, idx in enumerate(trace_indices):
            vis = (visibilities[0] if apply_single_val
                   else (visibilities[j] if j < len(visibilities) else None))
            if idx < len(traces):
                grp = traces[idx].get("legendgroup")
                if grp and vis is True:
                    trues.add(grp)

        # Lebih dari 1 grup diubah ke True → reset/show-all
        if len(trues) > 1:
            return None

        # Tepat 1 grup diubah ke True → isolasi grup tersebut
        if len(trues) == 1:
            return list(trues)[0]

        # Semua menjadi legendonly → temukan item yang masih visible (tidak di-hide)
        is_all_legendonly = (
            (apply_single_val and visibilities[0] == "legendonly") or
            (not apply_single_val and all(v == "legendonly" for v in visibilities))
        )
        if is_all_legendonly:
            hidden_set = set(trace_indices)
            for i, trace in enumerate(traces):
                if i not in hidden_set:
                    grp   = trace.get("legendgroup")
                    x_val = trace.get("x")
                    # Lewati dummy trace (x=[None])
                    if grp and x_val is not None and x_val != [None]:
                        return grp

        return None
    except Exception:
        return None
