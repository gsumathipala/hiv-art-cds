"""Concentration–time curves drawn from SmPC §5.2 pharmacokinetic parameters.

A one-compartment model with first-order absorption, purely illustrative: it shows the *shape*
of accumulation, trough cover and the long tail of the injectables, not predicted concentrations
for any individual. Parameters are the population values quoted in the SmPC.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from html import escape
from typing import List, Optional, Sequence, Tuple

from ..knowledge.citations import smpc_claim


@dataclass(frozen=True)
class Profile:
    code: str
    name: str
    half_life_h: float
    tmax_h: float
    interval_h: float  # dosing interval
    ic50_label: str = ""  # what the dashed line represents
    ic50_fraction: float = 0.0  # as a fraction of steady-state Cmax, for illustration
    note: str = ""
    injectable: bool = False


# Half-lives and Tmax as quoted in the UK SmPC §5.2 (verified by tools/verify_smpc.py).
_HL = r"half.?life"  # SmPCs mix hyphen and non-breaking hyphen
DTG = smpc_claim("tivicay", "5.2", r"terminal " + _HL + r" of ~14 hours")
BIC = smpc_claim("biktarvy", "5.2", r"plasma bictegravir " + _HL + r" was 17")
DOR = smpc_claim("pifeltro", "5.2", r"terminal " + _HL + r" \(t1/2\) of approximately 15 hours")
RPV = smpc_claim("edurant", "5.2", r"terminal elimination " + _HL + r" of rilpivirine is approximately 45 hours")
CAB_INJ = smpc_claim("vocabria_inj", "5.2", r"apparent terminal phase " + _HL + r" is absorption-rate limited")
RPV_INJ = smpc_claim("rekambys", "5.2", r"apparent " + _HL + r" of rilpivirine", r"13-28 weeks")
LEN = smpc_claim("sunlenca_inj", "5.2", r"median " + _HL + r" following oral and subcutaneous administration")

PROFILES: Tuple[Profile, ...] = (
    Profile("DTG", "Dolutegravir 50 mg once daily", 14, 2.5, 24, "Protein-adjusted IC90", 0.08,
            "Terminal half-life about 14 hours — comfortable once-daily cover with a wide trough margin."),
    Profile("DOR", "Doravirine 100 mg once daily", 15, 2, 24, "", 0.0,
            "Terminal half-life about 15 hours."),
    Profile("RPV", "Rilpivirine 25 mg once daily (oral)", 45, 4, 24, "", 0.0,
            "Long half-life (about 45 hours) means a slow approach to steady state and a slow washout."),
    Profile("RAL", "Raltegravir 400 mg twice daily", 9, 1, 12, "", 0.0,
            "Short half-life and sharp peaks and troughs — the reason for twice-daily dosing and its low "
            "barrier to resistance."),
    Profile("CAB-LA", "Cabotegravir injection, every 2 months", 1080, 168, 1440, "", 0.0,
            "Apparent half-life of 5–12 weeks after injection. The long tail is why an alternative regimen must "
            "start within 2 months of the last injection — sub-therapeutic concentrations select resistance.",
            injectable=True),
    Profile("RPV-LA", "Rilpivirine injection, every 2 months", 1800, 72, 1440, "", 0.0,
            "Apparent half-life of 13–28 weeks — rilpivirine persists even longer than cabotegravir.",
            injectable=True),
    Profile("LEN", "Lenacapavir injection, every 6 months", 2400, 2016, 4368, "", 0.0,
            "Subcutaneous depot with a half-life of 8–12 weeks, supporting 6-monthly dosing.", injectable=True),
)

PROFILES_BY_CODE = {p.code: p for p in PROFILES}

W, H = 880, 300
LEFT, RIGHT, TOP, BOTTOM = 56, 20, 22, 42


def _concentration(t: float, p: Profile, doses: Sequence[float]) -> float:
    """Sum of one-compartment first-order absorption/elimination contributions from each dose."""
    ke = math.log(2) / p.half_life_h
    ka = math.log(2) / max(p.tmax_h / 3, 0.2)
    if abs(ka - ke) < 1e-9:
        ka *= 1.05
    total = 0.0
    for start in doses:
        if t < start:
            continue
        dt = t - start
        total += (ka / (ka - ke)) * (math.exp(-ke * dt) - math.exp(-ka * dt))
    return max(total, 0.0)


def curve(code: str, doses_count: int = 8, stop_after: Optional[int] = None) -> str:
    """SVG of the concentration–time curve. ``stop_after`` doses then shows the washout tail."""
    p = PROFILES_BY_CODE[code]
    n = doses_count
    given = n if stop_after is None else min(stop_after, n)
    doses = [i * p.interval_h for i in range(given)]
    span = p.interval_h * (n + (3 if p.injectable else 2))
    steps = 400
    points = [(t, _concentration(t, p, doses)) for t in (span * i / steps for i in range(steps + 1))]
    peak = max(c for _, c in points) or 1.0
    x = lambda t: LEFT + t / span * (W - LEFT - RIGHT)  # noqa: E731
    y = lambda c: H - BOTTOM - (c / peak) * (H - TOP - BOTTOM)  # noqa: E731
    path = " ".join(f"{'M' if i == 0 else 'L'}{x(t):.1f},{y(c):.1f}" for i, (t, c) in enumerate(points))
    out: List[str] = [f'<svg class="pk-curve" viewBox="0 0 {W} {H}" role="img" '
                      f'aria-label="Illustrative concentration-time curve for {escape(p.name)}">']
    out.append(f'<line x1="{LEFT}" y1="{H - BOTTOM}" x2="{W - RIGHT}" y2="{H - BOTTOM}" stroke="var(--line)"/>'
               f'<line x1="{LEFT}" y1="{TOP}" x2="{LEFT}" y2="{H - BOTTOM}" stroke="var(--line)"/>')
    unit, divisor = ("weeks", 168.0) if p.injectable else ("days", 24.0)
    for i in range(0, int(span / p.interval_h) + 1):
        t = i * p.interval_h
        if t > span:
            break
        out.append(f'<line x1="{x(t):.1f}" y1="{TOP}" x2="{x(t):.1f}" y2="{H - BOTTOM}" stroke="var(--line)" '
                   f'stroke-width=".5"/><text x="{x(t):.1f}" y="{H - BOTTOM + 15}" font-size="10" '
                   f'text-anchor="middle" fill="var(--ink-2)">{t / divisor:.0f}</text>')
        if i < given:
            out.append(f'<polygon points="{x(t):.1f},{H - BOTTOM - 6} {x(t) - 4:.1f},{H - BOTTOM + 2} '
                       f'{x(t) + 4:.1f},{H - BOTTOM + 2}" fill="var(--accent)"><title>Dose</title></polygon>')
    out.append(f'<text x="{(W) / 2:.0f}" y="{H - 6}" font-size="11" text-anchor="middle" '
               f'fill="var(--ink-2)">Time ({unit})</text>')
    out.append(f'<text x="14" y="{(H - TOP) / 2:.0f}" font-size="11" fill="var(--ink-2)" '
               f'transform="rotate(-90 14 {(H - TOP) / 2:.0f})" text-anchor="middle">Relative concentration</text>')
    if stop_after is not None and given < n:
        tail = x(doses[-1] + p.interval_h)
        out.append(f'<rect x="{tail:.1f}" y="{TOP}" width="{W - RIGHT - tail:.1f}" height="{H - TOP - BOTTOM}" '
                   f'fill="var(--bad)" opacity=".07"/><text x="{tail + 8:.1f}" y="{TOP + 14}" font-size="11" '
                   f'fill="var(--bad)">No further doses — declining tail</text>')
    out.append(f'<path d="{path}" fill="none" stroke="var(--brand-2)" stroke-width="2"/>')
    out.append("</svg>")
    return "".join(out)


BOOSTER_EXPLAINER = (
    "Boosters (ritonavir, cobicistat) are mechanism-based CYP3A inhibitors: they raise and flatten the curve of the "
    "partner protease inhibitor, lifting the trough above the inhibitory concentration. Inducers (rifampicin, "
    "carbamazepine, St John's wort) do the opposite, dropping the trough into the range where resistance is selected "
    "— which is why they are contraindicated with most third agents.")
