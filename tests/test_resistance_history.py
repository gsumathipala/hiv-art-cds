"""Step 1: cumulative genotype history, minority variants, Stanford HIVdb integration."""
import os

import pytest

from art_cds import hivdb
from art_cds.engine.resistance import interpret_history, parse_with_frequency
from art_cds.models import GenotypeTest, TreatmentStatus

from .conftest import run


def test_frequency_and_position_validation():
    found, bad = parse_with_frequency("K103N:12%, M184V(4), 103N, RT:Y181C, X999Q, K999N", "RT")
    assert found == [("K103N", 12.0), ("M184V", 4.0), ("103N", None), ("Y181C", None)]
    assert bad == ["X999Q", "K999N"]


def test_cumulative_history_keeps_archived_mutations():
    tests = [GenotypeTest(date="2019-01-01", rt="K103N"), GenotypeTest(date="2026-01-01", rt="M184V"),
             GenotypeTest(date="2026-02-01", source="proviral", integrase="R263K")]
    r = interpret_history(tests)
    assert r.mutations["RT"] == ["K103N", "M184V"] and r.mutations["IN"] == ["R263K"]
    assert r.level("EFV") == 5 and r.level("3TC") == 5 and r.level("DTG") >= 3
    assert r.archived_only == ["IN:R263K"]
    assert any("cumulative" in w for w in r.warnings)


def test_minority_variants_below_threshold_are_not_scored():
    r = interpret_history([GenotypeTest(rt="K103N:8%, M184V:60%")], threshold=20)
    assert r.level("EFV") == 1 and r.level("3TC") == 5
    assert r.minority == ["RT:K103N (8%)"]
    r = interpret_history([GenotypeTest(rt="K103N:8%")], threshold=5)
    assert r.level("EFV") == 5


def test_hivdb_is_used_when_enabled(monkeypatch):
    calls = []

    def fake(muts):
        calls.append(muts)
        return {"version": "HIVDB_TEST", "validation": [],
                "drugs": {"DTG": {"score": 45, "level": 4, "contributors": ["Q148H"]},
                          "3TC": {"score": 75, "level": 5, "contributors": ["M184V"]}}}

    monkeypatch.setattr(hivdb, "analyse_mutations", fake)
    r = interpret_history([GenotypeTest(rt="M184V", integrase="Q148H")], use_hivdb=True)
    assert calls == [("RT:M184V", "IN:Q148H")]
    assert r.source == "hivdb" and r.version == "Stanford HIVdb HIVDB_TEST" and r.level("DTG") == 4


def test_hivdb_failure_falls_back_to_local(monkeypatch):
    def boom(_):
        raise hivdb.HivdbError("Stanford HIVdb could not be reached (test)")

    monkeypatch.setattr(hivdb, "analyse_mutations", boom)
    r = interpret_history([GenotypeTest(rt="K103N")], use_hivdb=True)
    assert r.source == "local" and r.level("EFV") == 5
    assert any("fell back" in w for w in r.warnings)


def test_sequence_needs_hivdb():
    r = interpret_history([GenotypeTest(sequence=">x\nACGT" * 50)])
    assert any("not analysed" in w for w in r.warnings)


def test_history_drives_the_recommendation():
    from art_cds.models import GenotypeTest as G
    report, ok, ex = run(status=TreatmentStatus.SUPPRESSED, viral_load=20,
                         genotypes=(G(date="2015-01-01", rt="K103N"),))
    assert "dor_3tc_tdf" in ex or "rpv_ftc_taf" in ex  # NNRTI switch blocked by archived K103N history
    assert report.resistance.tests and report.resistance.mutations["RT"] == ["K103N"]


@pytest.mark.skipif(not os.environ.get("ART_CDS_LIVE"), reason="set ART_CDS_LIVE=1 to call Stanford HIVdb")
def test_live_hivdb():
    r = interpret_history([GenotypeTest(rt="K65R M184V")], use_hivdb=True)
    assert r.source == "hivdb" and r.level("3TC") == 5
