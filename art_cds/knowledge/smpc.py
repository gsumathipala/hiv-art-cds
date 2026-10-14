"""Read the parsed UK SmPCs written by ``tools/fetch_smpc.py``.

The SmPC is the source for everything shown about a product: appearance,
dosing, contraindications, interactions, pregnancy, adverse reactions and
pharmacology. This module loads the parsed JSON and offers a few structured
views over it (adverse-reaction grid, section text search).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DATA = Path(__file__).resolve().parent.parent / "data" / "smpc"

SECTION_ORDER = (
    "composition", "form", "indications", "posology", "contraindications", "warnings",
    "interactions", "pregnancy", "driving", "adverse_effects", "overdose", "pharmacodynamics",
    "pharmacokinetics", "preclinical", "excipients", "shelf_life", "storage", "container",
)

FREQUENCIES = ("very common", "common", "uncommon", "rare", "very rare", "not known")


@lru_cache(maxsize=None)
def load(key: str) -> Optional[Dict]:
    path = DATA / f"{key}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def available() -> List[str]:
    return sorted(p.stem for p in DATA.glob("*.json"))


def section(key: str, name: str) -> Optional[Dict]:
    doc = load(key)
    return doc["sections"].get(name) if doc else None


def section_text(key: str, name: str) -> str:
    sec = section(key, name)
    if not sec:
        return ""
    parts: List[str] = []
    for block in sec["blocks"]:
        if block["type"] in ("p", "h"):
            parts.append(block["text"])
        elif block["type"] == "list":
            parts.extend(block["items"])
        elif block["type"] == "table":
            parts.extend(" | ".join(row) for row in block["rows"])
    return "\n".join(parts)


def mentions(key: str, name: str, *patterns: str) -> bool:
    """True if every regex pattern occurs in the section (case-insensitive)."""
    text = section_text(key, name)
    return bool(text) and all(re.search(p, text, re.I) for p in patterns)


def appearance_text(key: str) -> str:
    """The SmPC §3 sentence that describes what the dose unit looks like."""
    sec = section(key, "form")
    if not sec:
        return ""
    texts = [b["text"] for b in sec["blocks"] if b["type"] in ("p", "list") and b.get("text")]
    for t in texts:
        if re.search(r"\b(tablet|capsule|suspension|solution)\b.*\b(white|yellow|pink|brown|red|orange|"
                     r"blue|green|grey|gray|beige|purple|violet|colourless|clear|debossed|imprinted)", t, re.I):
            return t
    return " ".join(texts)


# ------------------------------------------------------- adverse reactions
_FREQ_RE = re.compile(r"^(very common|common|uncommon|rare|very rare|not known|frequency not known)\b", re.I)


def _norm_freq(text: str) -> Optional[str]:
    m = _FREQ_RE.match(text.strip().strip(":").strip())
    if not m:
        return None
    f = m.group(1).lower()
    return "not known" if "not known" in f else f


def _split_reactions(text: str) -> List[str]:
    text = re.sub(r"\b[a-z]\b(?=[,;]|$)", "", text)  # stray footnote letters
    text = re.sub(r"\(\s*see (?:section|sections)[^)]*\)", "", text, flags=re.I)
    text = re.sub(r"\s*\^?\s*\d+(,\d+)*$", "", text)
    items = [re.sub(r"[\d^*†‡§#]+$", "", s).strip(" .;") for s in re.split(r",|;|\n", text)]
    return [i[0].upper() + i[1:] for i in items
            if i and len(i) > 2 and not i.lower().startswith("see ") and not i.startswith(("*", "†", "‡"))]


_FREQ_WORDS = r"very common|common|uncommon|rare|very rare|not known|frequency not known"
_FREQ_SEGMENT = re.compile(r"(?:^|[;.]\s*|\s)(" + _FREQ_WORDS + r")\s*[:\-–]\s*(.*?)(?=(?:[;.]\s*|\s)(?:"
                           + _FREQ_WORDS + r")\s*[:\-–]|$)", re.I | re.S)
_SOC_WORDS = ("disorder", "infection", "investigation", "condition", "injur", "neoplasm", "skin", "gastrointestinal",
              "respiratory", "haematolog", "metabolism", "nervous", "psychiatr", "musculoskeletal", "hepato")


def _looks_like_soc(text: str) -> bool:
    t = text.strip().rstrip(":").lower()
    return 3 < len(t) < 110 and not t.endswith(".") and _norm_freq(t) is None and any(w in t for w in _SOC_WORDS)


def _segments(text: str):
    """'common: headache; uncommon: dizziness' -> [('common','headache'), ('uncommon','dizziness')]."""
    return [(_norm_freq(m.group(1)) or "", m.group(2)) for m in _FREQ_SEGMENT.finditer(text)]


def adverse_grid(key: str) -> Dict[str, Dict[str, List[str]]]:
    """Map system-organ class -> frequency -> reactions from SmPC §4.8.

    SmPCs lay this out in several ways; handled here:
      * SOC header rows followed by ``Frequency | reactions`` rows;
      * ``SOC | frequency | reactions`` and ``SOC | reactions | frequency`` rows;
      * ``SOC | common: a, b; uncommon: c`` cells;
      * ``SOC | very common | common | uncommon ...`` column layouts;
      * paragraphs: an SOC heading followed by ``Common: a, b`` lines.
    Anything it cannot read is left out — the full §4.8 text is always shown too.
    """
    sec = section(key, "adverse_effects")
    grid: Dict[str, Dict[str, List[str]]] = {}
    if not sec:
        return grid

    def add(soc: str, freq: str, text: str) -> None:
        soc = soc.strip().rstrip(":").strip()
        if not soc or not freq or not text:
            return
        bucket = grid.setdefault(soc, {})
        for r in _split_reactions(text):
            if r not in bucket.setdefault(freq, []):
                bucket[freq].append(r)

    def rows():
        for block in sec["blocks"]:
            if block["type"] == "table":
                yield "table", block["rows"]
            elif block["type"] in ("p", "h"):
                yield "text", [[block["text"]]]
            elif block["type"] == "list":
                yield "text", [[i] for i in block["items"]]

    soc = ""
    for kind, table in rows():
        header = [c.lower() for c in table[0]] if table else []
        col_freqs = [_norm_freq(c) for c in header]
        if kind == "table" and sum(1 for f in col_freqs if f) >= 2:  # frequencies as columns
            for row in table[1:]:
                for i, cell in enumerate(row[1:], start=1):
                    if row and i < len(col_freqs) and col_freqs[i] and cell.strip():
                        add(row[0], col_freqs[i], cell)
            continue
        for row in table:
            cells = [c for c in row if c.strip()]
            if not cells:
                continue
            if len(cells) == 1:
                cell = cells[0]
                segs = _segments(cell) if _norm_freq(cell) else []
                if segs and soc:
                    for f, t in segs:
                        add(soc, f, t)
                elif _looks_like_soc(cell):
                    soc = cell
                continue
            if kind == "text":
                continue
            first_freq, last_freq = _norm_freq(cells[0]), _norm_freq(cells[-1])
            if _looks_like_soc(cells[0]):
                soc = cells[0]
                rest = cells[1:]
            else:
                rest = cells
            if not soc:
                continue
            if _norm_freq(rest[0]) and len(rest) >= 2 and len(_segments(" ".join(rest))) <= 1:
                add(soc, _norm_freq(rest[0]) or "", " ".join(rest[1:]))  # freq | reactions
            elif last_freq and len(rest) >= 2 and not first_freq:
                add(soc, last_freq, " ".join(rest[:-1]))  # reactions | freq
            else:
                for f, t in _segments(" ; ".join(rest)):  # "common: a; uncommon: b"
                    add(soc, f, t)
    return {s: freqs for s, freqs in grid.items() if any(freqs.values())}


def frequency_counts(key: str) -> List[Tuple[str, int]]:
    grid = adverse_grid(key)
    return [(f, sum(len(v.get(f, [])) for v in grid.values())) for f in FREQUENCIES]


# ------------------------------------------------------- pharmacology quick facts
PK_FACTS = (
    ("Half-life", r"half[- ]li(fe|ves)"),
    ("Protein binding", r"(protein|plasma)[- ]bin(ding|d)|bound to (human )?plasma"),
    ("Time to peak", r"\b(T\s*max|t\s*max|peak (plasma )?concentrations?)\b"),
    ("Metabolism", r"metaboli[sz](ed|m)\b.*\b(CYP|UGT|hydrolys|phosphorylat|esterase|cathepsin)"),
    ("Elimination", r"(excreted|eliminated|recovered) (in|via|primarily|mainly|predominantly)"),
    ("Food effect", r"(with food|fed|high[- ]fat|meal)"),
)


def _sentences(text: str) -> List[str]:
    out: List[str] = []
    for line in text.split("\n"):
        if " | " in line or len(line) < 40:  # table rows and sub-headings
            continue
        out.extend(s.strip() for s in re.split(r"(?<=[.])\s+(?=[A-Z(])", line) if s.strip())
    return out


def pk_facts(key: str) -> List[Tuple[str, str]]:
    """The first SmPC §5.2 sentence that states each pharmacokinetic property."""
    sentences = _sentences(section_text(key, "pharmacokinetics"))
    out = []
    for label, pattern in PK_FACTS:
        hit = next((s for s in sentences if re.search(pattern, s, re.I) and len(s) < 600), None)
        if hit:
            out.append((label, hit))
    return out


def mechanism_sentence(key: str) -> str:
    sentences = _sentences(section_text(key, "pharmacodynamics"))
    return next((s for s in sentences if re.search(r"mechanism|inhibit|binds", s, re.I)), "")
