"""HIV-2 and HIV-1/HIV-2 dual infection.

BHIVA's adult ART guideline (2025) has no HIV-2 section; the BHIVA pregnancy guideline (2025, §8.6)
does, and the SmPCs state which drugs lack HIV-2 activity. Outside pregnancy the twice-daily dosing
advice is extrapolated from the pregnancy guideline and flagged as needing HIV-2 expert input.
"""
from __future__ import annotations

from ...knowledge.drugs import NNRTI, drug_class
from ...models import Severity
from .base import bhiva, claim, finding, rule

NNRTI_HIV2 = claim("efavirenz", "5.1", r"does not significantly inhibit HIV-2 RT")
RPV_HIV1 = claim("edurant", "4.1", r"human immunodeficiency virus type 1 \(HIV.1\)")
DOR_HIV1 = claim("pifeltro", "4.1", r"human immunodeficiency virus type 1 \(HIV.1\)")
MVC_HIV2 = claim("celsentri", "5.1", r"activity of maraviroc against HIV-2 has not been evaluated")
DRV_HIV2 = claim("prezista", "5.1", r"laboratory strains of HIV-2")
PREG_HIV2 = bhiva("bhiva_pregnancy", "8.6", r"pregnant women/people with HIV-2 are treated with tenofovir DX plus "
                                            r"emtricitabine AND either twice-daily dolutegravir 50 mg or twice-daily "
                                            r"darunavir/ritonavir 600 mg/100 mg")
EXPERT = bhiva("bhiva_pregnancy", "8.6", r"experts with experience of managing HIV-2")


def involves_hiv2(p) -> bool:
    return p.virus_type in ("HIV-2", "HIV-1/HIV-2")


@rule("hiv2", "HIV-2")
def hiv2(regimen, ctx):
    p = ctx.patient
    if not involves_hiv2(p):
        return []
    out = []
    comps = set(regimen.components)
    if any(drug_class(c) == NNRTI for c in comps):
        out.append(finding("hiv2", Severity.EXCLUDE, "NNRTIs are intrinsically inactive against HIV-2.",
                           refs=(NNRTI_HIV2, RPV_HIV1, DOR_HIV1),
                           teaching="HIV-2 reverse transcriptase differs from HIV-1 at residues lining the NNRTI "
                                    "pocket (including 181 and 188), so NNRTIs cannot bind — intrinsic, not "
                                    "acquired, resistance."))
    if regimen.dual and not regimen.long_acting:
        out.append(finding("hiv2", Severity.CAUTION, "No data for two-drug regimens in HIV-2 — use three active drugs.",
                           -30, refs=(EXPERT,)))
    if "ATV" in comps:
        out.append(finding("hiv2", Severity.CAUTION,
                           "Atazanavir is less potent against HIV-2; BHIVA's HIV-2 recommendation uses darunavir/ritonavir "
                           "or dolutegravir.", -20, refs=(PREG_HIV2,)))
    if "DTG" in comps:
        out.append(finding("hiv2", Severity.BENEFIT, "Dolutegravir is active against HIV-2.", 5, refs=(PREG_HIV2,),
                           dose_change="Dolutegravir 50 mg twice daily for HIV-2 (BHIVA pregnancy §8.6; seek HIV-2 "
                                       "expert advice outside pregnancy)"))
    if "DRV" in comps and "RTV" in comps:
        out.append(finding("hiv2", Severity.BENEFIT, "Darunavir/ritonavir is active against HIV-2.", 5,
                           refs=(PREG_HIV2, DRV_HIV2),
                           dose_change="Darunavir 600 mg + ritonavir 100 mg twice daily for HIV-2 (BHIVA pregnancy §8.6)"))
    if "COBI" in comps:
        out.append(finding("hiv2", Severity.CAUTION, "HIV-2 guidance uses ritonavir-boosted darunavir twice daily; "
                           "cobicistat once daily is not studied for HIV-2.", -15, refs=(PREG_HIV2,)))
    return out
