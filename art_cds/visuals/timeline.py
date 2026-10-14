"""Viral load / CD4 / ART timeline as an inline SVG."""
from __future__ import annotations

import math
from datetime import date
from html import escape
from typing import Dict, List, Optional, Sequence, Tuple

from ..models import ArtEpisode, LabValue

W, H = 920, 300
LEFT, RIGHT, TOP, BOTTOM = 62, 56, 54, 36
BAND = 30  # ART band height
COLOURS = ["#2f6fb6", "#0f8b8d", "#8a4fbf", "#c0562b", "#6b8e23", "#a2367a", "#7a8494"]
LABEL_COLOUR = {"undetectable": "#1f7a4d", "blip": "#e6b422", "low-level viraemia": "#e07a1f",
                ">200 copies/mL": "#b3261e", "50–200 copies/mL — repeat": "#e6b422"}


def _d(s: str) -> Optional[date]:
    try:
        parts = [int(x) for x in s.split("-")]
        return date(parts[0], parts[1] if len(parts) > 1 else 1, parts[2] if len(parts) > 2 else 1)
    except (ValueError, IndexError):
        return None


def render(vls: Sequence[LabValue], cd4s: Sequence[LabValue], art: Sequence[ArtEpisode],
           labels: Sequence[Tuple[str, str]] = ()) -> str:
    dates = [_d(v.date) for v in list(vls) + list(cd4s)] + [_d(e.start) for e in art] + \
            [_d(e.stop) for e in art if e.stop]
    dates = [d for d in dates if d]
    if not dates:
        return ""
    today = date.today()
    lo, hi = min(dates), max(dates + ([today] if any(e.current for e in art) else []))
    if hi <= lo:
        hi = date(lo.year + 1, lo.month, 1)
    span = (hi - lo).days or 1
    plot_top = TOP + BAND + 8
    plot_h = H - plot_top - BOTTOM
    x = lambda d: LEFT + (d - lo).days / span * (W - LEFT - RIGHT)  # noqa: E731
    y_vl = lambda v: plot_top + plot_h * (1 - (math.log10(max(v, 10)) - 1) / 6)  # 10..10^7  # noqa: E731
    cd4_max = max([v.value for v in cd4s] + [500])
    cd4_max = math.ceil(cd4_max / 250) * 250
    y_cd4 = lambda v: plot_top + plot_h * (1 - v / cd4_max)  # noqa: E731
    label_of: Dict[str, str] = dict(labels)
    out: List[str] = [f'<svg class="timeline" viewBox="0 0 {W} {H}" role="img" '
                      f'aria-label="Viral load, CD4 and ART timeline">']
    # axes and gridlines
    for exp in range(1, 8):
        yy = y_vl(10 ** exp)
        out.append(f'<line x1="{LEFT}" y1="{yy:.1f}" x2="{W - RIGHT}" y2="{yy:.1f}" stroke="var(--line)" '
                   f'stroke-width=".6"/><text x="{LEFT - 6}" y="{yy + 3:.1f}" text-anchor="end" font-size="10" '
                   f'fill="var(--ink-2)">10{"⁰¹²³⁴⁵⁶⁷"[exp]}</text>')
    for thr, txt in ((50, "50"), (200, "200")):
        yy = y_vl(thr)
        out.append(f'<line x1="{LEFT}" y1="{yy:.1f}" x2="{W - RIGHT}" y2="{yy:.1f}" stroke="#b3261e" '
                   f'stroke-dasharray="4 3" stroke-width="1" opacity=".6"/><text x="{W - RIGHT + 4}" y="{yy + 3:.1f}" '
                   f'font-size="9.5" fill="#b3261e">{txt}</text>')
    out.append(f'<text x="14" y="{plot_top + plot_h / 2:.0f}" font-size="11" fill="var(--ink-2)" '
               f'transform="rotate(-90 14 {plot_top + plot_h / 2:.0f})" text-anchor="middle">HIV RNA copies/mL</text>')
    for tick in range(0, int(cd4_max) + 1, 250):
        out.append(f'<text x="{W - RIGHT + 30}" y="{y_cd4(tick) + 3:.1f}" font-size="9.5" fill="#7a5fb0" '
                   f'text-anchor="start">{tick}</text>')
    out.append(f'<text x="{W - 6}" y="{plot_top + plot_h / 2:.0f}" font-size="11" fill="#7a5fb0" '
               f'transform="rotate(90 {W - 6} {plot_top + plot_h / 2:.0f})" text-anchor="middle">CD4 cells/mm³</text>')
    for yr in range(lo.year, hi.year + 2):
        d = date(yr, 1, 1)
        if lo <= d <= hi:
            xx = x(d)
            out.append(f'<line x1="{xx:.1f}" y1="{plot_top}" x2="{xx:.1f}" y2="{H - BOTTOM}" stroke="var(--line)" '
                       f'stroke-width=".6"/><text x="{xx:.1f}" y="{H - BOTTOM + 14}" font-size="10" '
                       f'text-anchor="middle" fill="var(--ink-2)">{yr}</text>')
    # ART band
    out.append(f'<text x="{LEFT - 6}" y="{TOP + BAND / 2 + 4}" text-anchor="end" font-size="10" '
               f'fill="var(--ink-2)">ART</text>')
    for i, e in enumerate(sorted(art, key=lambda e: e.start)):
        s, t = _d(e.start), (_d(e.stop) if e.stop else hi)
        if not s or not t:
            continue
        x0, x1 = x(s), max(x(t), x(s) + 4)
        colour = COLOURS[i % len(COLOURS)]
        name = " + ".join(e.components) or e.regimen or "ART"
        why = f" — stopped: {e.reason_stopped}" if e.reason_stopped else ""
        out.append(f'<g><title>{escape(name)} {escape(e.start)}–{escape(e.stop or "now")}{escape(why)}</title>'
                   f'<rect x="{x0:.1f}" y="{TOP}" width="{x1 - x0:.1f}" height="{BAND}" rx="5" fill="{colour}" '
                   f'opacity=".85"/><text x="{x0 + 5:.1f}" y="{TOP + BAND / 2 + 4}" font-size="10.5" fill="#fff" '
                   f'font-weight="600">{escape(name[: max(3, int((x1 - x0) / 6.2))])}</text></g>')
        if e.reason_stopped == "virological failure" and e.stop:
            out.append(f'<text x="{x1:.1f}" y="{TOP - 4}" font-size="12" text-anchor="middle" fill="#b3261e">✕</text>')
    # CD4 line
    pts = sorted(((_d(v.date), v) for v in cd4s if _d(v.date)), key=lambda p: p[0])
    if pts:
        path = " ".join(f"{'M' if i == 0 else 'L'}{x(d):.1f},{y_cd4(v.value):.1f}" for i, (d, v) in enumerate(pts))
        out.append(f'<path d="{path}" fill="none" stroke="#7a5fb0" stroke-width="1.6" stroke-dasharray="5 3"/>')
        for d, v in pts:
            out.append(f'<rect x="{x(d) - 3.5:.1f}" y="{y_cd4(v.value) - 3.5:.1f}" width="7" height="7" '
                       f'fill="#7a5fb0"><title>CD4 {v.value:.0f} ({v.date})</title></rect>')
    # viral load line + points
    pts = sorted(((_d(v.date), v) for v in vls if _d(v.date)), key=lambda p: p[0])
    if pts:
        path = " ".join(f"{'M' if i == 0 else 'L'}{x(d):.1f},{y_vl(v.value):.1f}" for i, (d, v) in enumerate(pts))
        out.append(f'<path d="{path}" fill="none" stroke="var(--ink)" stroke-width="1.6"/>')
        for d, v in pts:
            colour = LABEL_COLOUR.get(label_of.get(v.date, ""), "#1f7a4d" if v.censored or v.value < 50 else "#b3261e")
            tip = f"HIV RNA {v.display} ({v.date}) {label_of.get(v.date, '')}"
            if v.censored:
                out.append(f'<path d="M{x(d) - 5:.1f},{y_vl(v.value) - 4:.1f} L{x(d) + 5:.1f},{y_vl(v.value) - 4:.1f} '
                           f'L{x(d):.1f},{y_vl(v.value) + 5:.1f}Z" fill="var(--surface)" stroke="{colour}" '
                           f'stroke-width="2"><title>{escape(tip)}</title></path>')
            else:
                out.append(f'<circle cx="{x(d):.1f}" cy="{y_vl(v.value):.1f}" r="5" fill="{colour}" '
                           f'stroke="var(--surface)" stroke-width="1.5"><title>{escape(tip)}</title></circle>')
    out.append(f'<text x="{LEFT}" y="16" font-size="10.5" fill="var(--ink-2)">● viral load (▽ below limit) · '
               f'■ CD4 · bars = ART regimens (✕ stopped for failure) · dashed red lines = 50 and 200 copies/mL</text>')
    out.append("</svg>")
    return "".join(out)
