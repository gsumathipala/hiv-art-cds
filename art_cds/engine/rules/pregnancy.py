"""Pregnancy and conception (BHIVA pregnancy guidelines 2025; SmPC §4.6)."""
from __future__ import annotations

from ...models import Pregnancy, Severity, TreatmentStatus
from .base import bhiva, claim, finding, rule

_P = "bhiva_pregnancy"

# SmPC
COBI_SMPC = claim("rezolsta", "4.6", r"low darunavir exposure", r"should not be initiated during pregnancy")
DTG_SMPC = claim("tivicay", "4.6", r"Tsepamo", r"do not indicate an increased risk for neural tube defects")
BIC_SMPC = claim("biktarvy", "4.6", r"lower during pregnancy")
DOR_SMPC = claim("pifeltro", "4.6", r"preferable to avoid the use of doravirine during pregnancy")
EFV_SMPC = claim("efavirenz", "4.6", r"should not be used during pregnancy")
EFV_TEST = claim("efavirenz", "4.6", r"pregnancy testing before initiation")
RPV_SMPC = claim("edurant", "4.6", r"Lower exposures of rilpivirine were observed during pregnancy")
CAB_SMPC = claim("vocabria_inj", "4.6", r"not recommended during pregnancy unless")
RAL_SMPC = claim("isentress", "4.6", r"400 mg twice daily")
# BHIVA pregnancy 2025
COBI = bhiva(_P, "8.1", r"cobicistat should NOT be used as a booster in pregnancy")
COBI_PLANNING = bhiva(_P, "8.1", r"Darunavir/cobicistat can be initiated in those planning to conceive but cobicistat "
                                 r"must be switched to ritonavir")
DTG_FIRST = bhiva(_P, "8.3.1", r"First choice in the absence of renal or bone concerns")
BIC = bhiva(_P, "8.1", r"Bictegravir Limited pharmacokinetic and pregnancy outcome data")
DOR = bhiva(_P, "8.1", r"Insufficient human data available to establish safety in pregnancy")
EFV = bhiva(_P, "8.3.1", r"Non-preferred regimen due to side effect profile; may be used to manage drug interactions "
                         r"with tuberculosis")
RPV = bhiva(_P, "8.3.1", r"Not recommended if viral load >100,000 copies/mL or CD4 count <200")
RPV_PPI = bhiva(_P, "8.1", r"interaction with proton pump inhibitors and other acid-lowering drugs which are routinely "
                           r"given during caesarean section")
TWO_DRUG = bhiva(_P, "8.1", r"not in combinations with fewer than three agents in pregnancy")
LA = bhiva(_P, "8.1", r"we recommend 4-weekly dosing during pregnancy")
DRV_BID = bhiva(_P, "8.2", r"Darunavir/ritonavir should be administered as 600 mg/100 mg twice daily if initiated in "
                           r"pregnancy")
RAL_BID = bhiva(_P, "8.2", r"Raltegravir should be administered as 400 mg twice daily if initiated or continued")
ABC_CVD = bhiva(_P, "8.3.1", r"Estimated 10-year risk of cardiovascular disease should be <10%")


@rule("pregnancy", "Pregnancy")
def pregnancy(regimen, ctx):
    p = ctx.patient
    comps = set(regimen.components)
    out = []
    if p.pregnancy is Pregnancy.PREGNANT:
        starting = p.status is not TreatmentStatus.SUPPRESSED
        if "COBI" in comps:
            out.append(finding("pregnancy", Severity.EXCLUDE,
                               "Cobicistat should not be used as a booster in pregnancy — darunavir levels fall; switch "
                               "to ritonavir.", refs=(COBI, COBI_SMPC)))
        if "DTG" in comps:
            out.append(finding("pregnancy", Severity.BENEFIT,
                               "Dolutegravir is BHIVA's recommended anchor in pregnancy; large surveillance studies show no "
                               "increase in neural tube defects.", 10, refs=(DTG_SMPC,),
                               teaching="The 2018 Tsepamo signal (0.94% vs 0.12%) fell to background levels as data "
                                        "accrued — a lesson in early pharmacovigilance signals."))
            if regimen.id == "dtg_ftc_tdf" and not p.has("osteoporosis") and (p.crcl is None or p.crcl >= 60):
                out.append(finding("pregnancy", Severity.BENEFIT,
                                   "Dolutegravir + FTC/tenofovir disoproxil is BHIVA's first choice in pregnancy without "
                                   "renal or bone concerns.", 5, refs=(DTG_FIRST,)))
        if "BIC" in comps:
            out.append(finding("pregnancy", Severity.CAUTION,
                               "Limited pharmacokinetic and pregnancy-outcome data for bictegravir — use only if the "
                               "benefit outweighs the risk, with extra viral-load monitoring.", -15,
                               refs=(BIC, BIC_SMPC)))
        if "DOR" in comps:
            out.append(finding("pregnancy", Severity.CAUTION,
                               "Insufficient data to establish doravirine's safety in pregnancy.", -25,
                               refs=(DOR, DOR_SMPC)))
        if "EFV" in comps:
            tb = p.takes("rifampicin") or p.has("active_tb")
            out.append(finding("pregnancy", Severity.INFO if tb else Severity.CAUTION,
                               "Efavirenz is non-preferred in pregnancy because of side effects; it is an option to manage "
                               "TB drug interactions and can be switched postpartum.", 0 if tb else -15,
                               refs=(EFV, EFV_SMPC)))
        if "RPV" in comps and not regimen.long_acting:
            if starting and ((p.viral_load or 0) > 100_000 or (p.cd4 is not None and p.cd4 < 200)):
                out.append(finding("pregnancy", Severity.EXCLUDE,
                                   "Rilpivirine is not recommended in pregnancy with viral load > 100,000 copies/mL or "
                                   "CD4 < 200.", refs=(RPV,)))
            out.append(finding("pregnancy", Severity.INFO,
                               "Rilpivirine levels fall in pregnancy, and the acid-lowering drugs routinely given at "
                               "caesarean section interact with it — plan ahead.", refs=(RPV_PPI, RPV_SMPC)))
        if regimen.long_acting:
            out.append(finding("pregnancy", Severity.CAUTION,
                               "Limited data for long-acting cabotegravir/rilpivirine in pregnancy — consider switching to "
                               "an oral three-drug regimen; continuing needs MDT discussion.", -25,
                               refs=(LA, CAB_SMPC), dose_change="If continued in pregnancy, BHIVA recommends 4-weekly "
                                                                "injections (consider TDM)"))
        if "RAL" in comps:
            out.append(finding("pregnancy", Severity.INFO, "Pregnancy data are for raltegravir 400 mg twice daily.",
                               refs=(RAL_BID, RAL_SMPC),
                               dose_change="Raltegravir 400 mg twice daily in pregnancy (not 1,200 mg once daily)"))
        if "DRV" in comps and "RTV" in comps and starting:
            out.append(finding("pregnancy", Severity.INFO,
                               "Darunavir levels fall with once-daily dosing in pregnancy.", refs=(DRV_BID,),
                               dose_change="Darunavir 600 mg + ritonavir 100 mg twice daily when started in pregnancy"))
        if "ABC" in comps and p.has("cvd"):
            out.append(finding("pregnancy", Severity.CAUTION,
                               "BHIVA requires an estimated 10-year cardiovascular risk < 10% for abacavir in pregnancy.",
                               -25, refs=(ABC_CVD,)))
        if regimen.dual and not regimen.long_acting:
            out.append(finding("pregnancy", Severity.CAUTION,
                               "No data for two-drug combinations in pregnancy — only with MDT discussion and closer "
                               "viral-load monitoring.", -25, refs=(TWO_DRUG,)))
    elif p.pregnancy is Pregnancy.PLANNING:
        if "COBI" in comps:
            out.append(finding("pregnancy", Severity.CAUTION,
                               "Planning conception — cobicistat can be started but must be switched to ritonavir once "
                               "pregnant.", -10, refs=(COBI_PLANNING,)))
        if "DTG" in comps:
            out.append(finding("pregnancy", Severity.BENEFIT,
                               "Dolutegravir has reassuring conception-safety data.", 5, refs=(DTG_SMPC,)))
        if "BIC" in comps:
            out.append(finding("pregnancy", Severity.CAUTION,
                               "Bictegravir has limited pregnancy data — an alternative, not preferred, anchor around "
                               "conception.", -8, refs=(BIC,)))
        if "EFV" in comps:
            out.append(finding("pregnancy", Severity.CAUTION, "Efavirenz is non-preferred in pregnancy.", -15,
                               refs=(EFV, EFV_TEST)))
        if "DOR" in comps:
            out.append(finding("pregnancy", Severity.CAUTION, "Insufficient pregnancy data for doravirine.", -10,
                               refs=(DOR,)))
    return out
