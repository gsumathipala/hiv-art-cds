"""Hazard log (DCB0129 style). Initial developer assessment — to be reviewed and owned by the
organisation's Clinical Safety Officer before any clinical use."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

SEVERITY = ("Minor", "Significant", "Considerable", "Major", "Catastrophic")
LIKELIHOOD = ("Very low", "Low", "Medium", "High", "Very high")
# DCB0129 risk matrix: rows = likelihood (very low..very high), columns = severity (minor..catastrophic)
MATRIX = (
    (1, 1, 2, 2, 3),
    (1, 2, 2, 3, 4),
    (2, 2, 3, 3, 4),
    (2, 3, 3, 4, 5),
    (3, 4, 4, 5, 5),
)
RISK_LABEL = {1: "Acceptable", 2: "Acceptable where cost of further reduction outweighs benefit",
              3: "Undesirable — mitigate", 4: "Mandatory elimination or control", 5: "Unacceptable"}


@dataclass(frozen=True)
class Hazard:
    id: str
    hazard: str
    cause: str
    effect: str
    controls: Tuple[str, ...]
    severity: str
    likelihood: str  # residual, after controls

    @property
    def risk(self) -> int:
        return MATRIX[LIKELIHOOD.index(self.likelihood)][SEVERITY.index(self.severity)]


HAZARDS: Tuple[Hazard, ...] = (
    Hazard("H01", "Contraindicated regimen ranked as suitable",
           "Interaction, renal/hepatic limit or licensing restriction missing from the knowledge base",
           "Toxicity or loss of efficacy",
           ("Every SmPC/BHIVA statement verified against source text in CI (tools/verify_smpc.py)",
            "Interaction matrix states blank != safe; Liverpool checker linked on every page",
            "Excluded regimens shown with reasons for clinician review"), "Major", "Low"),
    Hazard("H02", "Outdated product information", "SmPC revised after download",
           "Recommendation based on superseded dosing or contraindications",
           ("SmPC revision date shown on every product page", "tools/check_updates.py re-fetches and diffs SmPCs "
            "and re-runs verification", "Knowledge-base version on every report"), "Considerable", "Low"),
    Hazard("H03", "Resistance under-estimated", "Local approximate scores; archived mutations not entered; "
           "minority variants below threshold", "Regimen with reduced activity chosen; further resistance",
           ("Stanford HIVdb algorithm available", "Cumulative genotype across all tests incl. proviral DNA",
            "Minority variants and local-mode use flagged in alerts", "MDT prompt for multiclass resistance"),
           "Major", "Low"),
    Hazard("H04", "Data-entry error", "Wrong units (creatinine µmol/L vs mg/dL), wrong patient, mistyped mutation",
           "Wrong renal or resistance assessment",
           ("Range validation on all numbers", "Mutation notation and gene positions validated",
            "Patient summary echoed on the report"), "Considerable", "Medium"),
    Hazard("H05", "Automation bias", "Clinician accepts top-ranked regimen without review",
           "Inappropriate regimen for factors the tool does not model",
           ("Education mode by default", "All reasons and citations displayed", "Scope and limitations stated",
            "No automatic prescribing"), "Considerable", "Medium"),
    Hazard("H06", "External service unavailable or returns error", "Stanford HIVdb outage",
           "Resistance not scored as expected",
           ("Automatic fall-back to local scores with a visible warning", "Source of scores shown on the report"),
           "Significant", "Low"),
    Hazard("H07", "Paediatric or HIV-2 patient assessed with adult HIV-1 logic", "Out-of-scope use",
           "Wrong dosing or ineffective drugs",
           ("Critical alert for age < 18", "HIV-2 mode excludes NNRTIs and disables HIV-1 resistance scoring"),
           "Major", "Very low"),
    Hazard("H08", "Confidential data disclosed", "Audit or case files containing clinical data; data sent to HIVdb",
           "Information-governance breach",
           ("Audit log stores an input hash only by default", "HIVdb opt-in; no identifiers sent",
            "Case files saved only to the user's own device"), "Considerable", "Low"),
)
