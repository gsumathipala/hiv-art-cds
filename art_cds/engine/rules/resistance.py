"""Genotypic resistance: activity of every drug in the regimen."""
from __future__ import annotations

from ...knowledge.drugs import BOOSTERS, CYTIDINE, HIGH_BARRIER, TENOFOVIR, name
from ...knowledge.guidelines import BHIVA_ART
from ...models import Severity, TreatmentStatus, guideline
from ..resistance import regimen_gss
from .base import finding, rule

HIVDB = guideline("Stanford HIVdb-style penalty scores (simplified)")


@rule("resistance", "Resistance")
def resistance(regimen, ctx):
    res = ctx.resistance
    if res is None:
        return []
    p = ctx.patient
    out = []
    failure = p.status is TreatmentStatus.FAILURE
    bhiva = guideline(BHIVA_ART)

    for drug in regimen.core_agents:
        s = res.get(drug)
        if s is None:
            continue
        muts = ", ".join(m for m in s.contributors if not m.startswith("(")) or "none"
        if s.level >= 5:
            out.append(finding("resistance", Severity.EXCLUDE,
                               f"{name(drug)}: high-level resistance ({muts}).", refs=(HIVDB,)))
        elif s.level == 4:
            if failure and drug == "DTG":
                out.append(finding("resistance", Severity.CAUTION,
                                   f"Dolutegravir: intermediate resistance ({muts}) — reduced activity even at "
                                   "twice-daily dosing.", -30, refs=(HIVDB, bhiva),
                                   dose_change="Dolutegravir 50 mg twice daily (integrase resistance)"))
            elif failure and drug == "DRV":
                out.append(finding("resistance", Severity.CAUTION,
                                   f"Darunavir: intermediate resistance ({muts}).", -25, refs=(HIVDB,),
                                   dose_change="Darunavir 600 mg + ritonavir 100 mg twice daily (darunavir RAMs)"))
            else:
                out.append(finding("resistance", Severity.EXCLUDE,
                                   f"{name(drug)}: intermediate resistance ({muts}).", refs=(HIVDB,)))
        elif s.level == 3:
            out.append(finding("resistance", Severity.CAUTION, f"{name(drug)}: low-level resistance ({muts}).", -15,
                               refs=(HIVDB,),
                               dose_change="Dolutegravir 50 mg twice daily" if failure and drug == "DTG" else None))
        elif s.level == 2:
            out.append(finding("resistance", Severity.CAUTION,
                               f"{name(drug)}: potential low-level resistance ({muts}).", -5, refs=(HIVDB,)))

    tenofovir_active = any(res.level(d) <= 2 for d in regimen.nrtis if d in TENOFOVIR)
    for drug in regimen.nrtis:
        s = res.get(drug)
        muts = ", ".join(m for m in s.contributors if not m.startswith("(")) or "none"
        if s.level >= 4:
            if failure:
                out.append(finding("resistance", Severity.INFO,
                                   f"{name(drug)}: {s.label.lower()} ({muts}) — counts {s.activity:g} toward the GSS.",
                                   refs=(HIVDB,)))
            elif (p.status is TreatmentStatus.SUPPRESSED and drug in CYTIDINE and tenofovir_active
                  and regimen.anchor in ("BIC", "DTG") and not regimen.dual):
                out.append(finding("resistance", Severity.CAUTION,
                                   f"{name(drug)}: {s.label.lower()} ({muts}). With fully active tenofovir and a "
                                   "second-generation INSTI, suppression has been maintained after switch despite "
                                   "M184V/I.", -10, refs=(bhiva,)))
            else:
                out.append(finding("resistance", Severity.EXCLUDE,
                                   f"{name(drug)}: {s.label.lower()} ({muts}) — first-line and switch regimens need "
                                   "fully active NRTIs.", refs=(HIVDB,)))
        elif s.level == 3:
            out.append(finding("resistance", Severity.CAUTION, f"{name(drug)}: low-level resistance ({muts}).", -10,
                               refs=(HIVDB,)))

    if failure:
        gss = regimen_gss(regimen.components, res) or 0.0
        core_full = all(res.level(d) <= 2 for d in regimen.core_agents)
        high_barrier = any(d in HIGH_BARRIER for d in regimen.core_agents if d not in BOOSTERS)
        if gss >= 2:
            out.append(finding("resistance", Severity.BENEFIT,
                               f"Genotypic susceptibility score {gss:g}: at least two fully active drugs.", 5,
                               refs=(bhiva,)))
        elif gss >= 1 and core_full and high_barrier:
            out.append(finding("resistance", Severity.CAUTION,
                               f"GSS {gss:g}: relies on a fully active high-barrier anchor with partly active NRTIs "
                               "(supported by NADIA for dolutegravir and by trials of boosted darunavir).",
                               -15 if gss >= 1.5 else -25, refs=(bhiva,),
                               teaching="The GSS adds each drug's predicted activity. Below 2, success depends on "
                                        "the anchor's genetic barrier — acceptable for dolutegravir or boosted "
                                        "darunavir, risky for anything else."))
        else:
            out.append(finding("resistance", Severity.EXCLUDE,
                               f"GSS {gss:g}: fewer than two active drugs and no fully active high-barrier anchor.",
                               refs=(bhiva,)))
    return out
