"""Abacavir and HLA-B*57:01."""
from __future__ import annotations

from ...models import LabResult, Severity
from .base import claim, finding, rule

ABACAVIR_HLA = claim("triumeq", "4.1", r"HLA-B\*5701", r"should not be used")
ABACAVIR_SCREEN = claim("triumeq", "4.1", r"screening for carriage of the HLA-B\*5701")


@rule("hla", "HLA-B*57:01")
def hla(regimen, ctx):
    if "ABC" not in regimen.components:
        return []
    status = ctx.patient.hla_b5701
    if status is LabResult.POSITIVE:
        return [finding("hla", Severity.EXCLUDE,
                        "HLA-B*57:01 positive — abacavir is contraindicated (hypersensitivity reaction).",
                        refs=(ABACAVIR_HLA,))]
    if status is LabResult.UNKNOWN:
        return [finding("hla", Severity.EXCLUDE,
                        "HLA-B*57:01 status unknown — screen before starting abacavir.",
                        refs=(ABACAVIR_SCREEN,),
                        teaching="About 5–8% of white European people carry HLA-B*57:01; screening has "
                                 "almost eliminated immunologically confirmed abacavir hypersensitivity.")]
    return [finding("hla", Severity.INFO,
                    "HLA-B*57:01 negative — hypersensitivity is still possible; counsel the patient and never "
                    "rechallenge after a suspected reaction.", refs=(ABACAVIR_SCREEN,))]
