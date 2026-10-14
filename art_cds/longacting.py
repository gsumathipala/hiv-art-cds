"""Long-acting injectable ART: schedules, the ±7-day window, missed injections, oral bridging,
failure-risk assessment — cabotegravir + rilpivirine (Vocabria + Rekambys) and lenacapavir (Sunlenca).

Every rule is taken from the UK SmPC §4.2/§4.4 and cited; the citations are verified with the rest.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, Sequence, Tuple

from .knowledge.citations import bhiva, smpc_claim
from .models import Ref

SCHEDULE_Q2M = smpc_claim("vocabria_inj", "4.2", r"Two months after last initiation injection and every 2 months",
                          r"up to 7 days before or after the date of the every 2 month")
SCHEDULE_Q1M = smpc_claim("vocabria_inj", "4.2", r"single 400 mg monthly intramuscular injection",
                          r"up to 7 days before or after the date of the monthly 400 mg")
LEAD_IN = smpc_claim("vocabria_inj", "4.2", r"approximately one month \(at least 28 days\)")
MISSED_Q1M = smpc_claim("vocabria_inj", "4.2", r"Continue with the monthly 400 mg injection schedule as soon as possible",
                        r"Re-initiate the patient on the 600 mg dose, and then continue to follow the monthly")
MISSED_Q2M = smpc_claim("vocabria_inj", "4.2", r"Injection 3 or later", r"≤3 months",
                        r"followed by a second 600 mg initiation injection one month later")
BRIDGE_Q1M = smpc_claim("vocabria_inj", "4.2", r"replace up to 2 consecutive monthly injection visits")
BRIDGE_Q2M = smpc_claim("vocabria_inj", "4.2", r"replace one, 2-monthly injection visit")
TAIL = smpc_claim("vocabria_inj", "4.2", r"no later than one month after the final injection of Vocabria when dosed "
                                         r"monthly and no later than two months")
RISK = smpc_claim("vocabria_inj", "4.4", r"combination of at least 2 of the following baseline factors",
                  r"archived rilpivirine resistance mutations, HIV-1 subtype A6/A1, or BMI ≥30")
RISK_Q2M = smpc_claim("vocabria_inj", "4.4", r"virologic failure occurs more often when these patients are treated "
                                             r"according to the every 2 month dosing regimen")
LA_MONITORING = bhiva("bhiva_art", "5.11", r"Two-monthly HIV RNA quantification for the first 6.12 months")
LEN_SCHEDULE = smpc_claim("sunlenca_inj", "4.2", r"Day 15", r"once every 6 months \(26 weeks\)",
                          r"\+/- 2 weeks")
LEN_MISSED = smpc_claim("sunlenca_inj", "4.2", r"more than 28 weeks have elapsed since the last injection")

# Rilpivirine resistance-associated mutations (BHIVA 2025 §5.11 list)
RPV_RAMS = ("L100I", "K101E", "K101P", "E138A", "E138G", "E138K", "E138Q", "E138R", "V179L", "V179F", "Y181C",
            "Y181I", "Y181V", "Y188L", "H221Y", "F227C", "F227L", "M230I", "M230L")
RPV_RAMS_REF = bhiva("bhiva_art", "5.11", r"not recognised rilpivirine RAMs \(i\.e\. L100I, K101E/P, E138A/G/K/Q/R")


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    day = min(d.day, [31, 29 if (d.year + y) % 4 == 0 and ((d.year + y) % 100 or (d.year + y) % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m])
    return date(d.year + y, m + 1, day)


@dataclass(frozen=True)
class Visit:
    number: int
    target: date
    window: Tuple[date, date]
    doses: str
    label: str


def cab_rpv_schedule(first_injection: date, every_2_months: bool = True, oral_lead_in: bool = False,
                     visits: int = 8) -> List[Visit]:
    out: List[Visit] = []
    if oral_lead_in:
        start = first_injection - timedelta(days=28)
        out.append(Visit(0, start, (start, start), "Vocabria 30 mg + Edurant 25 mg tablets daily with a meal",
                         "Oral lead-in (at least 28 days) — optional"))
    for n in range(1, visits + 1):
        if every_2_months:
            months = 0 if n == 1 else 1 if n == 2 else 1 + 2 * (n - 2)
            doses = "Vocabria 600 mg + Rekambys 900 mg IM (gluteal)"
            label = "Initiation injection" if n <= 2 else "Continuation (every 2 months)"
        else:
            months = n - 1
            doses = ("Vocabria 600 mg + Rekambys 900 mg IM" if n == 1 else "Vocabria 400 mg + Rekambys 600 mg IM")
            label = "Initiation injection" if n == 1 else "Continuation (monthly)"
        target = add_months(first_injection, months)
        window = (target, target) if n == 1 else (target - timedelta(days=7), target + timedelta(days=7))
        out.append(Visit(n, target, window, doses, label))
    return out


def missed_injection(last_injection: date, on: date, every_2_months: bool, missed_visit: int) -> Tuple[str, Ref]:
    """Recommendation from SmPC Table 4 (monthly) or Table 5 (every 2 months). missed_visit is 2, 3, 4…"""
    elapsed = (on - last_injection).days
    if not every_2_months:
        if elapsed <= 61:
            return "≤ 2 months since the last injection: continue the monthly 400 mg/600 mg schedule as soon as " \
                   "possible.", MISSED_Q1M
        return "> 2 months since the last injection: re-initiate with 600 mg/900 mg, then continue monthly " \
               "400 mg/600 mg.", MISSED_Q1M
    limit = 61 if missed_visit == 2 else 92
    span = "2 months" if missed_visit == 2 else "3 months"
    if elapsed <= limit:
        return f"≤ {span} since the last injection: resume 600 mg/900 mg as soon as possible, then every 2 months.", \
            MISSED_Q2M
    return f"> {span} since the last injection: re-initiate with 600 mg/900 mg, a second 600 mg/900 mg one month " \
           "later, then every 2 months.", MISSED_Q2M


def oral_bridge(last_injection: date, every_2_months: bool) -> Tuple[str, Ref]:
    if every_2_months:
        start = add_months(last_injection, 2)
        return (f"Oral cabotegravir 30 mg + rilpivirine 25 mg daily can replace ONE 2-monthly visit: start "
                f"{start:%d %b %Y} (±7 days) and give the next injection on the day oral dosing finishes. Use another "
                "fully suppressive oral regimen if more than 2 months is needed.", BRIDGE_Q2M)
    start = add_months(last_injection, 1)
    return (f"Oral cabotegravir 30 mg + rilpivirine 25 mg daily can replace up to TWO monthly visits: start "
            f"{start:%d %b %Y} (±7 days) and resume injections on the day oral dosing finishes.", BRIDGE_Q1M)


@dataclass(frozen=True)
class FailureRisk:
    factors: Tuple[str, ...]
    unknown: Tuple[str, ...]

    @property
    def high(self) -> bool:
        return len(self.factors) >= 2


def failure_risk(mutations: Sequence[str], subtype: str, bmi: Optional[float]) -> FailureRisk:
    """SmPC §4.4: ≥ 2 of archived RPV RAMs, subtype A6/A1, BMI ≥ 30 raises the risk of virological failure."""
    factors, unknown = [], []
    rams = []
    for m in mutations:
        hit = re.match(r"^([A-Z])?(\d+)([A-Z*]+)$", m)
        if hit and any(r[1:-1] == hit.group(2) and r[-1] in hit.group(3) for r in RPV_RAMS):
            rams.append(m)
    rams = sorted(set(rams))
    if rams:
        factors.append("rilpivirine RAMs (" + ", ".join(rams) + ")")
    if subtype in ("A1", "A6"):
        factors.append(f"subtype {subtype}")
    elif not subtype:
        unknown.append("subtype")
    if bmi is not None and bmi >= 30:
        factors.append(f"BMI {bmi:.1f}")
    elif bmi is None:
        unknown.append("BMI")
    return FailureRisk(tuple(factors), tuple(unknown))


def lenacapavir_schedule(day1: date, visits: int = 4) -> List[Visit]:
    out = [Visit(0, day1, (day1, day1), "600 mg orally (2 × 300 mg)", "Day 1"),
           Visit(0, day1 + timedelta(days=1), (day1 + timedelta(days=1),) * 2, "600 mg orally", "Day 2"),
           Visit(0, day1 + timedelta(days=7), (day1 + timedelta(days=7),) * 2, "300 mg orally", "Day 8")]
    inj = day1 + timedelta(days=14)
    out.append(Visit(1, inj, (inj, inj), "927 mg subcutaneous (2 × 1.5 mL)", "Day 15 — first injection"))
    for n in range(2, visits + 1):
        inj = inj + timedelta(weeks=26)
        out.append(Visit(n, inj, (inj - timedelta(weeks=2), inj + timedelta(weeks=2)), "927 mg subcutaneous",
                         "Every 26 weeks (±2 weeks)"))
    return out


def ics(visits: Sequence[Visit], title: str) -> str:
    """An iCalendar file of the injection visits (all-day events)."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ART Navigator UK//long-acting schedule//EN"]
    for v in visits:
        lines += ["BEGIN:VEVENT", f"UID:{title.replace(' ', '')}-{v.target:%Y%m%d}-{v.number}@art-navigator",
                  f"DTSTAMP:{date.today():%Y%m%d}T000000Z",
                  f"DTSTART;VALUE=DATE:{v.target:%Y%m%d}",
                  f"SUMMARY:{title} — {v.label}",
                  f"DESCRIPTION:{v.doses}. Window {v.window[0]:%d %b %Y} to {v.window[1]:%d %b %Y}.",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
