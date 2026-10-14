"""Classify the viral-load course on ART (BHIVA adult ART guidelines 2025, sections 7.2–7.4).

Definitions used:
  * undetectable — < 50 copies/mL;
  * blip — a single 50–200 copies/mL result with undetectable results before and after (BHIVA §7.2);
  * low-level viraemia — two or more consecutive results of 50–200 copies/mL (BHIVA §7.3 describes it
    but gives no numeric rule; this is the tool's working definition);
  * suspected failure — a single result > 200 copies/mL, to be investigated with a rapid re-test (§7.4);
  * confirmed failure — two consecutive results > 200 copies/mL (the re-test confirming §7.4).
Only results on or after the start of ART count when an ART history is given.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from ..knowledge.citations import bhiva
from ..models import ArtEpisode, LabValue, Ref

BLIP = bhiva("bhiva_art", "7.2", r"single viral load of 50.200 copies/mL preceded and followed by an undetectable")
LLV = bhiva("bhiva_art", "7.3", r"context of low-level viraemia or repeated blips a high genetic barrier regimen")
FAIL = bhiva("bhiva_art", "7.4", r"single viral load of >200 copies/mL is investigated further")

UNDETECTABLE = "undetectable"
BLIP_ = "blip"
LLV_ = "low-level viraemia"
SUSPECTED = "suspected virological failure"
CONFIRMED = "confirmed virological failure"
NOT_SUPPRESSED = "not yet suppressed"


@dataclass
class VirologyAssessment:
    status: str
    message: str
    refs: Tuple[Ref, ...] = ()
    labels: List[Tuple[str, str]] = field(default_factory=list)  # (date, label) per result
    blips: int = 0

    @property
    def concerning(self) -> bool:
        return self.status in (LLV_, SUSPECTED, CONFIRMED) or self.blips >= 2


def _detectable(v: LabValue, limit: float = 50) -> bool:
    return not v.censored and v.value >= limit


def art_start(history: Sequence[ArtEpisode]) -> Optional[str]:
    starts = sorted(e.start for e in history if e.start)
    return starts[0] if starts else None


def classify(vls: Sequence[LabValue], history: Sequence[ArtEpisode] = ()) -> Optional[VirologyAssessment]:
    start = art_start(history)
    series = sorted((v for v in vls if not start or v.date >= start), key=lambda v: v.date)
    if not series:
        return None
    labels: List[Tuple[str, str]] = []
    blips = 0
    for i, v in enumerate(series):
        prev = series[i - 1] if i else None
        nxt = series[i + 1] if i + 1 < len(series) else None
        if not _detectable(v):
            labels.append((v.date, UNDETECTABLE))
        elif v.value <= 200:
            flanked = prev is not None and nxt is not None and not _detectable(prev) and not _detectable(nxt)
            if flanked:
                blips += 1
                labels.append((v.date, BLIP_))
            elif (prev and _detectable(prev) and prev.value <= 200) or (nxt and _detectable(nxt) and nxt.value <= 200):
                labels.append((v.date, LLV_))
            else:
                labels.append((v.date, "50–200 copies/mL — repeat"))
        else:
            labels.append((v.date, ">200 copies/mL"))

    last = series[-1]
    two_last = series[-2:] if len(series) >= 2 else []
    ever_suppressed = any(not _detectable(v) for v in series)
    if len(two_last) == 2 and all(_detectable(v, 201) for v in two_last):
        status = CONFIRMED if ever_suppressed or start else NOT_SUPPRESSED
        msg = ("Two consecutive viral loads > 200 copies/mL: assess adherence, interactions and tolerability, and send "
               "a resistance test while on the current regimen.")
        refs: Tuple[Ref, ...] = (FAIL,)
    elif _detectable(last, 201):
        status, refs = SUSPECTED, (FAIL,)
        msg = f"Latest viral load {last.display} copies/mL — re-test rapidly, with or without a resistance test."
    elif len(two_last) == 2 and all(_detectable(v) and v.value <= 200 for v in two_last):
        status, refs = LLV_, (LLV,)
        msg = ("Persistent low-level viraemia (50–200 copies/mL) — attempt resistance testing and use a high "
               "genetic-barrier regimen.")
    elif _detectable(last):
        status, refs = BLIP_, (BLIP,)
        msg = f"Latest viral load {last.display} copies/mL — repeat in 2–6 weeks; a single blip is usually not a concern."
    else:
        status, refs = UNDETECTABLE, ()
        msg = f"Undetectable at last test ({last.date})."
    if blips >= 2 and status == UNDETECTABLE:
        msg += f" {blips} previous blips — treat repeated blips like low-level viraemia."
        refs = (LLV,)
    elif blips:
        msg += f" ({blips} blip{'s' if blips > 1 else ''} on record.)"
    return VirologyAssessment(status, msg, refs, labels, blips)


def latest(values: Sequence[LabValue]) -> Optional[LabValue]:
    return max(values, key=lambda v: v.date) if values else None
