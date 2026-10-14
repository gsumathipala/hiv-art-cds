"""Drug–drug interactions with the patient's co-medications (SmPC §4.3/4.5)."""
from __future__ import annotations

from ...knowledge.interactions import ADJUST, AVOID, COMEDICATIONS_BY_KEY, CONTRAINDICATED, INTERACTIONS, lookup
from ...knowledge.drugs import name
from ...models import Severity, smpc
from .base import CLAIMS, finding, rule

for _i in INTERACTIONS:  # every table entry is a verifiable SmPC claim
    CLAIMS.append((_i.product, _i.section, _i.evidence))

_MAP = {
    CONTRAINDICATED: (Severity.EXCLUDE, 0.0),
    AVOID: (Severity.CAUTION, -35.0),
    ADJUST: (Severity.CAUTION, -8.0),
}


@rule("interactions", "Drug interactions")
def interactions(regimen, ctx):
    out = []
    for comed in sorted(ctx.patient.comedications):
        label = COMEDICATIONS_BY_KEY[comed].label
        for drug in regimen.components:
            ix = lookup(comed, drug)
            if ix is None:
                continue
            ref = smpc(ix.product, ix.section)
            text = f"{label} + {name(drug)}: {ix.message}"
            if regimen.long_acting and ix.oral_only:
                out.append(finding("interactions", Severity.INFO, text + " (Relevant to oral lead-in/bridging only.)",
                                   refs=(ref,)))
                continue
            severity, score = _MAP.get(ix.severity, (Severity.INFO, -2.0))
            out.append(finding("interactions", severity, text, score, refs=(ref,), dose_change=ix.dose_change))
    return out
