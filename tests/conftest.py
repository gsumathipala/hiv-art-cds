import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from art_cds import create_app  # noqa: E402
from art_cds.config import TestConfig  # noqa: E402
from art_cds.engine.recommender import recommend  # noqa: E402
from art_cds.knowledge import smpc  # noqa: E402
from art_cds.models import PatientProfile  # noqa: E402

needs_smpc = pytest.mark.skipif(not smpc.available(), reason="SmPCs not downloaded (python -m tools.fetch_smpc)")


@pytest.fixture
def client():
    return create_app(TestConfig).test_client()


def patient(**kw) -> PatientProfile:
    """A well-characterised ART-naive adult; override what the test is about."""
    from art_cds.models import LabResult

    base = dict(age=35, weight_kg=70, viral_load=40_000, cd4=450, crcl=110, hbsag=LabResult.NEGATIVE,
                hla_b5701=LabResult.NEGATIVE, genotype_available=True)
    base.update(kw)
    return PatientProfile(**base)


def run(**kw):
    report = recommend(patient(**kw))
    return report, {a.regimen.id: a for a in report.recommended}, {a.regimen.id: a for a in report.excluded}
