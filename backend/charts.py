"""
PNG charts of the stored history for Telegram (/night and the morning summary).

Two stacked panels on one time axis (temperature, humidity), each with its
comfort band; gaps where the sensor was off are left empty instead of being
bridged by a straight line. Needs matplotlib; without it render() returns None
and the bot falls back to text only.
"""
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BG, PANEL, INK, MUTED, GRID = "#04070C", "#0B1320", "#E2E8F0", "#94A3B8", "#1E293B"
TEMP, HUM, BAND = "#F97316", "#22D3EE", "#22C55E"


def _with_gaps(points: list[dict], step: int):
    """Times and values with a None between buckets more than 3 steps apart."""
    times, temps, hums = [], [], []
    for i, p in enumerate(points):
        if i and p["ts"] - points[i - 1]["ts"] > 3 * step:
            times.append(datetime.fromtimestamp(p["ts"] - step))
            temps.append(None)
            hums.append(None)
        times.append(datetime.fromtimestamp(p["ts"]))
        temps.append(p["temperature"])
        hums.append(p["humidity"])
    return times, temps, hums


def render(points: list[dict], step: int, thresholds, title: str) -> bytes | None:
    """`points` as returned by HistoryStore.series(). PNG bytes, or None."""
    if len(points) < 2:
        return None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
    except ImportError:
        logger.info("matplotlib not installed: charts are skipped")
        return None

    times, temps, hums = _with_gaps(points, step)
    span_h = (points[-1]["ts"] - points[0]["ts"]) / 3600
    fig, (ax_t, ax_h) = plt.subplots(2, 1, figsize=(10, 6.4), dpi=110, sharex=True,
                                     gridspec_kw={"hspace": 0.12})
    fig.patch.set_facecolor(BG)
    panels = (
        (ax_t, temps, TEMP, "Temperature (°C)", thresholds.TEMP_LOW, thresholds.TEMP_HIGH),
        (ax_h, hums, HUM, "Humidity (%)", thresholds.HUMIDITY_LOW, thresholds.HUMIDITY_HIGH),
    )
    for ax, values, color, label, low, high in panels:
        ax.set_facecolor(PANEL)
        ax.axhspan(low, high, color=BAND, alpha=0.08, lw=0)
        ax.axhline(high, color=BAND, alpha=0.35, lw=1, ls="--")
        ax.plot(times, values, color=color, lw=2, solid_capstyle="round")
        real = [v for v in values if v is not None]
        lo, hi = min(real + [low]), max(real + [high])
        pad = max((hi - lo) * 0.08, 0.5)
        ax.set_ylim(lo - pad, hi + pad)
        ax.set_ylabel(label, color=MUTED, fontsize=10)
        ax.grid(True, color=GRID, lw=0.8)
        ax.tick_params(colors=MUTED, labelsize=9)
        for side in ax.spines.values():
            side.set_visible(False)
        last = real[-1]
        ax.annotate(f"{last:.1f}" if color == TEMP else f"{last:.0f}", (times[-1], last),
                    xytext=(6, 0), textcoords="offset points", color=color, fontsize=10, va="center",
                    fontweight="bold")
    fmt = "%H:%M" if span_h <= 36 else "%a %d"
    ax_h.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
    ax_h.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=9, interval_multiples=True))
    fig.suptitle(title, color=INK, fontsize=13, x=0.06, ha="left", fontweight="bold")
    fig.text(0.06, 0.915, "Dashed line = upper comfort limit · shaded = comfort range", color=MUTED, fontsize=9)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=BG, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return buf.getvalue()
