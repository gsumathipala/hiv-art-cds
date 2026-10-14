"""The patient's priorities: tablet burden, injections, adherence, meals."""
from __future__ import annotations

from ...knowledge.drugs import HIGH_BARRIER, LOW_BARRIER
from ...knowledge.guidelines import BHIVA_ART, NICE_TA757
from ...models import Severity, guideline
from .base import claim, finding, rule

RPV_MEAL = claim("edurant", "4.2", r"(with a meal|with food)")


@rule("preferences", "Patient priorities")
def preferences(regimen, ctx):
    p = ctx.patient
    out = []
    if regimen.long_acting:
        if p.prefers_long_acting:
            out.append(finding("preferences", Severity.BENEFIT,
                               "Meets the patient's wish for long-acting injectable treatment.", 25,
                               refs=(guideline(NICE_TA757),)))
        else:
            out.append(finding("preferences", Severity.CAUTION,
                               "Needs clinic visits for intramuscular injections every 1–2 months.", -10))
        if p.adherence_concerns:
            out.append(finding("preferences", Severity.INFO,
                               "Missed injection visits risk resistance during the long pharmacokinetic tail — agree an "
                               "oral bridging plan."))
    elif regimen.single_tablet:
        out.append(finding("preferences", Severity.BENEFIT, "One tablet once daily.",
                           8 if p.prefers_single_tablet else 3))
    elif regimen.units_per_day >= 3 or regimen.twice_daily:
        out.append(finding("preferences", Severity.CAUTION,
                           f"Higher pill burden ({regimen.units_per_day:g} tablets/day"
                           f"{', twice-daily dosing' if regimen.twice_daily else ''}).",
                           -8 if p.prefers_single_tablet else -4))
    elif p.prefers_single_tablet:
        out.append(finding("preferences", Severity.CAUTION, "Two tablets a day rather than a single tablet.", -3))

    if p.adherence_concerns and not regimen.long_acting:
        if regimen.anchor in HIGH_BARRIER:
            out.append(finding("preferences", Severity.BENEFIT,
                               "High barrier to resistance is more forgiving of missed doses.", 10,
                               refs=(guideline(BHIVA_ART),)))
        elif regimen.anchor in LOW_BARRIER:
            out.append(finding("preferences", Severity.CAUTION,
                               "Low barrier to resistance — missed doses risk resistance.", -15,
                               refs=(guideline(BHIVA_ART),)))

    if p.food_insecurity and not regimen.long_acting:
        if "RPV" in regimen.components:
            out.append(finding("preferences", Severity.CAUTION,
                               "Rilpivirine must be taken with a meal for adequate absorption.", -20, refs=(RPV_MEAL,)))
        elif regimen.food.lower().startswith("with food"):
            out.append(finding("preferences", Severity.CAUTION, "Must be taken with food.", -8))
    return out
