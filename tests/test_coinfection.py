"""Step 8: co-infection logic — HBV serology, hepatitis C pairing, tuberculosis."""
from art_cds.models import LabResult, TreatmentStatus

from .conftest import run


def test_isolated_anti_hbc_discourages_tenofovir_free_regimens():
    report, ok, ex = run(hbsag=LabResult.NEGATIVE, anti_hbc=LabResult.POSITIVE, anti_hbs=LabResult.NEGATIVE)
    assert any("Isolated anti-HBc" in f.message for f in ok["dtg_3tc"].findings)
    assert any("Isolated anti-HBc" in a.message for a in report.alerts)
    assert not any("Isolated anti-HBc" in f.message for f in ok["bic_ftc_taf"].findings)


def test_occult_hepatitis_b_requires_tenofovir():
    _, _, ex = run(hbsag=LabResult.NEGATIVE, hbv_dna=120)
    assert "dtg_3tc" in ex and "dtg_abc_3tc" in ex


def test_hepatitis_c_pairing_is_listed():
    report, ok, _ = run(hcv=True)
    assert any("Compatible hepatitis C regimens" in f.message for f in ok["bic_ftc_taf"].findings)
    drv = ok.get("drvc_ftc_taf") or ok.get("drvr_ftc_taf")
    msg = next(f.message for f in drv.findings if "hepatitis C" in f.message)
    assert "Maviret" not in msg  # glecaprevir/pibrentasvir avoided with boosted darunavir


def test_tb_rules_follow_bhiva_tb_guideline():
    report, ok, ex = run(comorbidities=frozenset({"active_tb"}), comedications=frozenset({"rifampicin"}), cd4=40)
    assert "bic_ftc_taf" in ex and "dtg_3tc" in ex and "dtg_ftc_taf" in ex  # TAF/BIC/dual not recommended with TB
    assert "efv_plus_ftc_tdf" in ok and ok["efv_plus_ftc_tdf"].score > ok["dtg_ftc_tdf"].score
    assert any("within 2 weeks" in a.message for a in report.alerts)


def test_cns_tb_defers_art():
    report, _, _ = run(comorbidities=frozenset({"cns_tb"}), comedications=frozenset({"rifampicin"}))
    assert any("delayed for 8 weeks" in a.message for a in report.alerts)


def test_crag_screening_alerts():
    report, _, _ = run(cd4=60)
    assert any("cryptococcal antigen" in a.message for a in report.alerts)
    report, _, _ = run(cd4=60, crag=LabResult.POSITIVE)
    assert any("lumbar puncture" in a.message for a in report.alerts)


def test_tb_on_suppressive_art_does_not_interrupt():
    report, _, _ = run(status=TreatmentStatus.SUPPRESSED, viral_load=20,
                       comorbidities=frozenset({"active_tb"}), comedications=frozenset({"rifampicin"}))
    assert any("do not interrupt ART" in a.message for a in report.alerts)
