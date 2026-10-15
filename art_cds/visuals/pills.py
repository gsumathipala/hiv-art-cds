"""Draw each dose unit from its SmPC section 3 description.

Manufacturer photographs are copyrighted, so the app draws every tablet,
capsule and injection from the words of SmPC §3 — colour, shape, size in mm
and debossing — at true relative scale. The verbatim §3 text is always shown
under the drawing so the reader can check it.

A licensed photograph can replace a drawing: put it at
``art_cds/static/img/products/<product key>.(jpg|png|webp)``.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..knowledge import smpc

PHOTO_DIR = Path(__file__).resolve().parent.parent / "static" / "img" / "products"

# Colour words in SmPC §3 -> fill colours. Longest phrases are matched first.
COLOURS = {
    "purplish-brown": "#6f4656", "purplish brown": "#6f4656", "reddish-brown": "#8a4434",
    "brownish-red": "#8f3b32", "yellowish-brown": "#a77b3c", "light brown": "#b3875f",
    "pale yellow": "#f3e39b", "light yellow": "#f3e39b", "yellow-orange": "#f2b544",
    "dark yellow": "#e3b928", "yellow": "#f0cf47", "light orange": "#f6b67a", "orange": "#ee8f3c",
    "light pink": "#f5c6d0", "pale pink": "#f5c6d0", "pink": "#ef9bb0", "dark pink": "#d9688a",
    "red": "#c8463c", "brown": "#8a5a3c", "beige": "#e3d2b0", "light purple": "#b49ad0",
    "purple": "#7a4b8f", "violet": "#7a4b8f", "light blue": "#a8c6ec", "powder blue": "#b9d2ee",
    "blue": "#3f74c4", "light green": "#a9d6a0", "green": "#5aa262", "grey": "#9a9da3",
    "gray": "#9a9da3", "off-white": "#efe9d8", "white": "#f8f7f2", "black": "#333333",
    "colourless": "#eef3f7", "clear": "#eef3f7",
}
_COLOUR_RE = re.compile("|".join(sorted(map(re.escape, COLOURS), key=len, reverse=True)), re.I)

SHAPES = (
    ("capsule-shaped", "capsule"), ("capsule shaped", "capsule"), ("oblong", "capsule"),
    ("modified oval", "oval"), ("almond", "almond"), ("diamond", "diamond"), ("triangular", "triangle"),
    ("rectangular", "rect"), ("oval", "oval"), ("round", "round"), ("hard capsule", "hardcap"),
    ("capsule", "hardcap"),
)

PX_PER_MM = 7.0


@dataclass
class DoseUnit:
    kind: str  # tablet | hardcap | injection | other
    shape: str
    colour: str
    colour_word: str
    cap_colour: Optional[str]
    length_mm: Optional[float]
    width_mm: Optional[float]
    deboss: Tuple[str, ...]
    text: str  # the sentence it was read from


def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.;])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def _dimensions(s: str) -> Tuple[Optional[float], Optional[float]]:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:mm)?\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*mm", s)
    if m:
        a, b = (float(g.replace(",", ".")) for g in m.groups())
        return max(a, b), min(a, b)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*mm\s*(?:in\s+)?diameter|diameter\s*(?:of\s*)?(\d+(?:[.,]\d+)?)\s*mm", s)
    if m:
        d = float((m.group(1) or m.group(2)).replace(",", "."))
        return d, d
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*mm in length\D{0,6}(\d+(?:[.,]\d+)?)\s*mm in width", s)
    if m:
        return float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", "."))
    m = re.search(r"length\D{0,20}(\d+(?:[.,]\d+)?)\s*mm", s)
    if m:
        return float(m.group(1).replace(",", ".")), None
    return None, None


def _deboss(s: str) -> Tuple[str, ...]:
    quoted = re.findall(r"[“\"'‘]([^”“\"'’]{1,20})[”“\"'’]", s)
    if quoted:
        return tuple(q.strip() for q in quoted[:2])
    m = re.search(r"(?:debossed|imprinted|printed|marked)\s+with\s+([A-Z0-9][A-Z0-9 ]{0,12}?)\s+(?:on|in)\b", s)
    return (m.group(1).strip(),) if m else ()


def parse_units(text: str) -> List[DoseUnit]:
    units: List[DoseUnit] = []
    for s in _sentences(text):
        low = s.lower()
        colours = _COLOUR_RE.findall(re.sub(r"\b\w+(?:-\w+)?\s+ink\b", "", s))  # printing ink is not the body colour
        if not colours:
            # "Each tablet is approximately 15 mm x 8 mm." follows the description
            if units and units[-1].length_mm is None:
                length, width = _dimensions(s)
                if length:
                    units[-1].length_mm, units[-1].width_mm = length, width
                    units[-1].text += " " + s
            if units and not units[-1].deboss and _deboss(s):
                units[-1].deboss = _deboss(s)
                units[-1].text += " " + s
            continue
        if "suspension" in low or "solution" in low:
            kind, shape = "injection", "vial"
        elif re.search(r"\bcapsules?\b", low) and "capsule-shaped" not in low and "capsule shaped" not in low:
            kind, shape = "hardcap", "hardcap"
        elif "tablet" in low or any(w in low for w, _ in SHAPES[:-2]):
            kind = "tablet"
            shape = next((v for w, v in SHAPES if w in low and v != "hardcap"), "round")
        else:
            continue
        word = colours[0].lower()
        cap = None
        if kind == "hardcap":
            m_cap = re.search(r"(" + _COLOUR_RE.pattern + r")\s+(?:opaque\s+)?cap\b", s, re.I)
            m_body = re.search(r"(" + _COLOUR_RE.pattern + r")\s+(?:opaque\s+)?body\b", s, re.I)
            if m_cap:
                cap = COLOURS[m_cap.group(1).lower()]
            if m_body:
                word = m_body.group(1).lower()
        length, width = _dimensions(s)
        if shape == "round" and width is None and length is not None:
            width = length
        units.append(DoseUnit(kind, shape, COLOURS[word], word, cap, length, width, _deboss(s), s))
    return units


@lru_cache(maxsize=1)
def _appearance_facts() -> Dict[str, List[Dict]]:
    """Factual dose-unit attributes exported by tools/export_appearance.py (no SmPC prose)."""
    path = Path(__file__).resolve().parent.parent / "data" / "appearance.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def units_for(product_key: str) -> List[DoseUnit]:
    """Dose units from the downloaded SmPC, falling back to the committed appearance facts."""
    units = parse_units(smpc.appearance_text(product_key))
    if units:
        return units
    return [DoseUnit(**fields, text="") for fields in _appearance_facts().get(product_key, [])]


def photo_for(product_key: str) -> Optional[str]:
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (PHOTO_DIR / f"{product_key}.{ext}").exists():
            return f"img/products/{product_key}.{ext}"
    return None


# ------------------------------------------------------------------ SVG
def _shade(hex_colour: str, factor: float) -> str:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if factor < 1:
        r, g, b = (int(c * factor) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (factor - 1)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _text_colour(fill: str) -> str:
    h = fill.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "rgba(0,0,0,.42)" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "rgba(255,255,255,.55)"


def _face(unit: DoseUnit, cx: float, cy: float, w: float, h: float, label: str, uid: str) -> str:
    fill, edge = unit.colour, _shade(unit.colour, 0.72)
    grad = f"g{uid}"
    defs = (f'<defs><radialGradient id="{grad}" cx="38%" cy="32%" r="75%">'
            f'<stop offset="0" stop-color="{_shade(fill, 1.35)}"/><stop offset=".55" stop-color="{fill}"/>'
            f'<stop offset="1" stop-color="{_shade(fill, 0.85)}"/></radialGradient></defs>')
    paint = f'fill="url(#{grad})" stroke="{edge}" stroke-width="1.2"'
    x, y = cx - w / 2, cy - h / 2
    if unit.shape == "round":
        body = f'<ellipse cx="{cx}" cy="{cy}" rx="{w / 2}" ry="{h / 2}" {paint}/>'
    elif unit.shape == "capsule":
        body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" {paint}/>'
    elif unit.shape == "rect":
        body = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h * 0.22}" {paint}/>'
    elif unit.shape == "diamond":
        body = (f'<path d="M{cx - w / 2},{cy} Q{cx - w / 4},{cy - h / 2} {cx},{cy - h / 2} '
                f'Q{cx + w / 4},{cy - h / 2} {cx + w / 2},{cy} Q{cx + w / 4},{cy + h / 2} {cx},{cy + h / 2} '
                f'Q{cx - w / 4},{cy + h / 2} {cx - w / 2},{cy}Z" {paint}/>')
    elif unit.shape == "almond":
        body = (f'<path d="M{cx - w / 2},{cy} C{cx - w / 4},{cy - h * 0.62} {cx + w / 4},{cy - h * 0.62} '
                f'{cx + w / 2},{cy} C{cx + w / 4},{cy + h * 0.62} {cx - w / 4},{cy + h * 0.62} {cx - w / 2},{cy}Z" '
                f'{paint}/>')
    elif unit.shape == "triangle":
        body = (f'<path d="M{cx},{y} L{x + w},{y + h} L{x},{y + h}Z" stroke-linejoin="round" {paint}/>')
    else:  # oval
        body = f'<ellipse cx="{cx}" cy="{cy}" rx="{w / 2}" ry="{h / 2}" {paint}/>'
    sheen = (f'<ellipse cx="{cx - w * 0.12}" cy="{cy - h * 0.22}" rx="{w * 0.28}" ry="{h * 0.12}" '
             f'fill="#fff" opacity=".28"/>')
    txt = ""
    if label:
        size = max(7.0, min(h * 0.32, w / max(len(label), 1) * 1.45))
        txt = (f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" '
               f'font-family="Helvetica,Arial,sans-serif" font-weight="700" font-size="{size:.1f}" '
               f'fill="{_text_colour(fill)}" style="paint-order:stroke" stroke="{_shade(fill, 1.25)}" '
               f'stroke-width=".6">{escape(label)}</text>')
    return defs + body + sheen + txt


def _hardcap(unit: DoseUnit, cx: float, cy: float, w: float, h: float, uid: str) -> str:
    body_fill, cap_fill = unit.colour, unit.cap_colour or unit.colour
    x, y = cx - w / 2, cy - h / 2
    return (f'<defs><clipPath id="c{uid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}"/></clipPath>'
            f'</defs><g clip-path="url(#c{uid})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{body_fill}"/>'
            f'<rect x="{x}" y="{y}" width="{w * 0.48}" height="{h}" fill="{cap_fill}"/></g>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="none" '
            f'stroke="{_shade(body_fill, 0.7)}" stroke-width="1.2"/>'
            f'<line x1="{x + w * 0.48}" y1="{y + 1}" x2="{x + w * 0.48}" y2="{y + h - 1}" '
            f'stroke="{_shade(cap_fill, 0.7)}" stroke-width="1"/>'
            f'<ellipse cx="{cx - w * 0.15}" cy="{cy - h * 0.25}" rx="{w * 0.3}" ry="{h * 0.1}" fill="#fff" opacity=".3"/>')


def _vial(unit: DoseUnit, uid: str) -> Tuple[str, float, float]:
    liquid = unit.colour
    svg = (f'<rect x="22" y="6" width="36" height="12" rx="2" fill="#7b8794"/>'
           f'<rect x="26" y="16" width="28" height="8" fill="#c9d1d9"/>'
           f'<rect x="14" y="24" width="52" height="86" rx="8" fill="#eef3f7" stroke="#9aa7b4" stroke-width="1.5"/>'
           f'<rect x="16" y="52" width="48" height="56" rx="6" fill="{liquid}" stroke="{_shade(liquid, .8)}"/>'
           f'<rect x="18" y="58" width="44" height="30" rx="3" fill="#fff" opacity=".85"/>'
           f'<text x="40" y="76" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="8" '
           f'fill="#445">IM</text><rect x="20" y="30" width="6" height="74" rx="3" fill="#fff" opacity=".5"/>')
    return svg, 80, 116


def svg_for(unit: DoseUnit, uid: str = "0", faces: int = 2) -> str:
    """Front (and back) of one dose unit, to scale, with a 10 mm scale bar."""
    if unit.kind == "injection":
        inner, w, h = _vial(unit, uid)
        return (f'<svg class="pill-svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
                f'aria-label="{escape(unit.colour_word)} suspension for injection">{inner}</svg>')
    length = unit.length_mm or (unit.width_mm or 10.0)
    width = unit.width_mm or (length * 0.5 if unit.shape in ("capsule", "oval", "hardcap", "almond") else length)
    w, h = length * PX_PER_MM, width * PX_PER_MM
    pad, gap, bar = 8, 18, 10 * PX_PER_MM
    faces = 1 if unit.kind == "hardcap" else faces
    total_w = pad * 2 + faces * w + (faces - 1) * gap
    total_h = pad * 2 + h + 22
    cy = pad + h / 2
    parts = []
    if unit.kind == "hardcap":
        parts.append(_hardcap(unit, pad + w / 2, cy, w, h, uid))
    else:
        labels = list(unit.deboss) + ["", ""]
        parts.append(_face(unit, pad + w / 2, cy, w, h, labels[0], f"{uid}a"))
        if faces == 2:
            parts.append(_face(unit, pad + w + gap + w / 2, cy, w, h, labels[1], f"{uid}b"))
    by = pad + h + 14
    parts.append(f'<g class="scale"><line x1="{pad}" y1="{by}" x2="{pad + bar}" y2="{by}" stroke="currentColor" '
                 f'stroke-width="1.5"/><line x1="{pad}" y1="{by - 3}" x2="{pad}" y2="{by + 3}" stroke="currentColor"/>'
                 f'<line x1="{pad + bar}" y1="{by - 3}" x2="{pad + bar}" y2="{by + 3}" stroke="currentColor"/>'
                 f'<text x="{pad + bar + 5}" y="{by + 3.5}" font-size="9" fill="currentColor" '
                 f'font-family="Helvetica,Arial,sans-serif">10 mm</text></g>')
    label = f"{unit.colour_word} {unit.shape} {unit.kind}"
    if unit.length_mm:
        label += f", about {unit.length_mm:g} mm"
    return (f'<svg class="pill-svg" viewBox="0 0 {total_w:.0f} {total_h:.0f}" width="{total_w:.0f}" '
            f'height="{total_h:.0f}" role="img" aria-label="{escape(label)}">{"".join(parts)}</svg>')
