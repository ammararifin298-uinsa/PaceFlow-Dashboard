# =============================================================================
# pages/benchmark/callbacks.py — Callbacks Halaman Benchmark PaceFlow
# Fitur: tombol "Jalankan Ulang Benchmark" menjalankan benchmark.py di background
#        dengan polling interval untuk update progress
# Safety: timeout 120s, hanya 1 proses sekaligus, tidak bisa dijalankan
#         jika belum ada data CSV di folder Data/
# =============================================================================

import os, json, time, subprocess, sys, threading
from dash import Input, Output, State, no_update, html, callback_context
from layout.design_tokens import C, F, rgba
from layout.components import info_box, ico

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BENCH_PY   = os.path.join(_ROOT, "benchmark.py")
_BENCH_JSON = os.path.join(_ROOT, "benchmark_results.json")
_DATA_DIR   = os.path.join(_ROOT, "Data")

# State shared between callbacks
_state = {
    "running": False,
    "proc": None,
    "started_at": 0,
    "log": [],
    "error": None,
    "done": False,
}
_lock = threading.Lock()

TIMEOUT_S = 120  # max 2 menit


def _required_csvs():
    """Cek apakah CSV yang dibutuhkan ada di Data/."""
    needed = ["race_results.csv", "races.csv",
              "driver_standings.csv", "pit_stops.csv", "qualifying.csv"]
    missing = [f for f in needed if not os.path.exists(os.path.join(_DATA_DIR, f))]
    return missing


def _start_benchmark():
    """Jalankan benchmark.py sebagai subprocess. Thread-safe."""
    with _lock:
        if _state["running"]:
            return False, "Benchmark sudah berjalan."
        missing = _required_csvs()
        if missing:
            return False, f"File CSV tidak ditemukan di Data/: {', '.join(missing)}"
        if not os.path.exists(_BENCH_PY):
            return False, "benchmark.py tidak ditemukan."

        _state["running"] = True
        _state["done"]    = False
        _state["error"]   = None
        _state["log"]     = []
        _state["started_at"] = time.time()

        def _run():
            try:
                proc = subprocess.Popen(
                    [sys.executable, _BENCH_PY],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=_ROOT,
                )
                _state["proc"] = proc
                for line in proc.stdout:
                    _state["log"].append(line.rstrip())
                    # Timeout guard
                    if time.time() - _state["started_at"] > TIMEOUT_S:
                        proc.kill()
                        _state["error"] = f"Timeout setelah {TIMEOUT_S}s."
                        break
                proc.wait()
                if proc.returncode != 0 and not _state["error"]:
                    _state["error"] = f"Proses selesai dengan kode: {proc.returncode}"
            except Exception as e:
                _state["error"] = str(e)
            finally:
                _state["running"] = False
                _state["done"]    = True
                _state["proc"]    = None

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return True, "ok"


def register_callbacks(app):

    @app.callback(
        Output("bench-run-result",  "children"),
        Output("bench-progress",    "children"),
        Output("bench-interval",    "disabled"),
        Output("store-bench-ts",    "data"),
        Input("btn-run-benchmark",  "n_clicks"),
        Input("bench-interval",     "n_intervals"),
        State("store-bench-ts",     "data"),
        prevent_initial_call=True,
    )
    def handle_benchmark(n_clicks, n_intervals, ts):
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        # ── Klik tombol: mulai benchmark ──────────────────────────────────
        if trigger == "btn-run-benchmark":
            if not n_clicks:
                return no_update, no_update, no_update, no_update

            ok, msg = _start_benchmark()
            if not ok:
                return (
                    info_box(f"❌ {msg}", C["red"]),
                    html.Span(),
                    True,   # interval tetap disabled
                    ts,
                )
            progress = html.Div([
                html.Div(style=dict(
                    height="3px", background=C["blue"],
                    borderRadius="2px", marginBottom="8px",
                    animation="pulse 1.5s ease-in-out infinite",
                )),
                html.Span("⏳ Benchmark berjalan... (maks. 2 menit)",
                    style=dict(fontSize="11px", color=C["muted"], fontFamily=F)),
            ])
            return (
                html.Span(),
                progress,
                False,       # aktifkan interval polling
                int(time.time()),
            )

        # ── Interval polling: cek status ──────────────────────────────────
        if trigger == "bench-interval":
            with _lock:
                running = _state["running"]
                done    = _state["done"]
                error   = _state["error"]
                log     = list(_state["log"])

            if not done and running:
                elapsed = int(time.time() - _state["started_at"])
                lines_shown = log[-5:] if log else ["Menginisialisasi..."]
                progress = html.Div([
                    html.Div(style=dict(
                        height="3px", background=C["blue"],
                        borderRadius="2px", marginBottom="8px",
                    )),
                    html.Div([
                        html.Span(f"⏳ Sedang berjalan ({elapsed}s)...",
                            style=dict(fontSize="11px", color=C["blue"],
                                       fontFamily=F, fontWeight="600",
                                       display="block", marginBottom="6px")),
                        html.Div(
                            html.Pre("\n".join(lines_shown),
                                style=dict(fontSize="10px", color=C["muted"],
                                           fontFamily="monospace", margin="0",
                                           whiteSpace="pre-wrap")),
                            style=dict(
                                background=C["grid"],
                                border=f"1px solid {C['border']}",
                                borderRadius="6px", padding="8px 12px",
                            )
                        ),
                    ]),
                ])
                return no_update, progress, False, ts

            # Done — reload page via store update to re-trigger page render
            if done:
                if error:
                    result = info_box(
                        f"❌ Benchmark gagal: {error}\n\nLog terakhir:\n"
                        + "\n".join(log[-10:]),
                        C["red"]
                    )
                    return result, html.Span(), True, int(time.time())

                # Sukses — tampilkan notifikasi, trigger page re-render
                result = info_box(
                    "✅ **Benchmark selesai!** Halaman akan diperbarui otomatis.",
                    C["green"]
                )
                # Return new ts → triggers page re-render via store-page
                return result, html.Span(), True, int(time.time())

        return no_update, no_update, no_update, no_update

    # ── Ketika bench selesai (store-bench-ts berubah) → re-render page ───
    @app.callback(
        Output("store-page", "data", allow_duplicate=True),
        Input("store-bench-ts", "data"),
        State("store-page", "data"),
        prevent_initial_call=True,
    )
    def refresh_after_bench(ts, current_page):
        if not ts or current_page != "benchmark":
            return no_update
        # Hanya re-render jika benchmark selesai sukses
        with _lock:
            if _state["done"] and not _state["error"]:
                return "benchmark"
        return no_update
