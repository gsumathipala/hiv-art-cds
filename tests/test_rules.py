"""Behaviour of the rule modules, through the recommender."""
from art_cds.models import ChildPugh, LabResult, Pregnancy, Severity, TreatmentStatus

from .conftest import needs_smpc, run


def test_uncomplicated_first_line_prefers_insti_regimens():
    report, ok, _ = run()
    assert report.top.regimen.anchor in ("BIC", "DTG")
    assert report.top.tier == "preferred"


def test_hla_positive_excludes_abacavir():
    _, ok, ex = run(hla_b5701=LabResult.POSITIVE)
    assert "dtg_abc_3tc" in ex and "dtg_abc_3tc" not in ok


def test_hla_unknown_excludes_abacavir():
    _, _, ex = run(hla_b5701=LabResult.UNKNOWN)
    assert "dtg_abc_3tc" in ex


def test_hbv_requires_tenofovir_plus_cytidine():
    _, ok, ex = run(hbsag=LabResult.POSITIVE)
    assert "dtg_3tc" in ex and "dtg_abc_3tc" in ex
    assert all({"TDF", "TAF"} & set(a.regimen.components) for a in ok.values())


def test_hbv_unknown_excludes_two_drug_regimens():
    _, _, ex = run(hbsag=LabResult.UNKNOWN)
    assert "dtg_3tc" in ex


@needs_smpc
def test_rifampicin():
    _, ok, ex = run(comedications=frozenset({"rifampicin"}))
    assert "bic_ftc_taf" in ex and "drvc_ftc_taf" in ex and "dor_3tc_tdf" in ex
    dtg = ok["dtg_ftc_tdf"]
    assert any("twice daily" in d for d in dtg.dose_changes)


@needs_smpc
def test_pregnancy_excludes_cobicistat_and_favours_dolutegravir():
    report, ok, ex = run(sex="female", pregnancy=Pregnancy.PREGNANT)
    assert "drvc_ftc_taf" in ex and "drvc_ftc_tdf" in ex
    assert "DTG" in report.top.regimen.components


@needs_smpc
def test_renal_limits_from_smpc():
    _, ok, ex = run(crcl=25)
    for rid in ("bic_ftc_taf", "dtg_ftc_taf", "dtg_ftc_tdf", "dtg_3tc", "dtg_abc_3tc", "dor_3tc_tdf"):
        assert rid in ex, rid


@needs_smpc
def test_rezolsta_not_started_below_70_with_ftc_tdf():
    _, _, ex = run(crcl=65)
    assert "drvc_ftc_tdf" in ex


@needs_smpc
def test_severe_hepatic_impairment():
    _, _, ex = run(child_pugh=ChildPugh.C)
    assert "bic_ftc_taf" in ex and "drvc_ftc_taf" in ex and "drvr_ftc_taf" in ex


@needs_smpc
def test_rilpivirine_viral_load_limit_in_pregnancy():
    _, _, ex = run(sex="female", pregnancy=Pregnancy.PREGNANT, viral_load=250_000)
    assert "rpv_ftc_taf" in ex and "rpv_ftc_tdf" in ex


def test_efavirenz_fdc_is_licensed_for_switch_only():
    _, _, ex = run()
    assert "efv_ftc_tdf" not in ex  # not offered at all in first-line...
    _, ok, _ = run(status=TreatmentStatus.SUPPRESSED, viral_load=20)
    assert "efv_ftc_tdf" in ok  # ...but offered for suppressed switch


def test_long_acting_only_for_suppressed_without_failure():
    _, ok, _ = run(status=TreatmentStatus.SUPPRESSED, viral_load=20, prefers_long_acting=True)
    assert "cab_rpv_la" in ok
    _, _, ex = run(status=TreatmentStatus.SUPPRESSED, viral_load=20, failed_classes=frozenset({"NNRTI"}))
    assert "cab_rpv_la" in ex


def test_failure_with_k65r_m184v_relies_on_high_barrier_anchor():
    report, ok, ex = run(status=TreatmentStatus.FAILURE, failed_classes=frozenset({"NNRTI", "NRTI"}),
                         viral_load=15_000, rt_mutations="K65R M184V K103N")
    assert report.top.regimen.anchor in ("DTG", "DRV")
    assert "efv_plus_ftc_tdf" in ex
    assert ok["dtg_azt_3tc"].gss == 2.0


def test_rapid_start_limits_choice():
    _, ok, _ = run(rapid_start=True, genotype_available=False, hla_b5701=LabResult.UNKNOWN,
                   hbsag=LabResult.UNKNOWN, viral_load=None, cd4=None)
    assert set(ok) <= {"bic_ftc_taf", "dtg_ftc_taf", "dtg_ftc_tdf", "drvc_ftc_taf", "drvc_ftc_tdf",
                       "drvr_ftc_taf", "drvr_ftc_tdf"}


def test_every_finding_has_a_known_severity_and_excluded_have_reasons():
    report, _, _ = run(hbsag=LabResult.POSITIVE, crcl=40)
    for a in report.excluded:
        assert any(f.severity is Severity.EXCLUDE for f in a.findings)


# ---- BHIVA 2025 interim update and BHIVA pregnancy 2025

def test_rilpivirine_and_atazanavir_are_not_first_line():
    report, ok, ex = run()
    offered = set(ok) | set(ex)
    assert not offered & {"rpv_ftc_taf", "rpv_ftc_tdf", "atvr_ftc_tdf"}
    _, ok, _ = run(status=TreatmentStatus.SUPPRESSED, viral_load=20)
    assert "rpv_ftc_taf" in ok and ok["rpv_ftc_taf"].tier_label == "Acceptable for switch"


def test_raltegravir_first_line_needs_viral_load_below_100000():
    _, _, ex = run(viral_load=150_000)
    assert "ral_ftc_taf" in ex


def test_efavirenz_first_line_only_with_tb_or_pregnancy():
    _, _, ex = run()
    assert "efv_plus_ftc_tdf" in ex
    _, ok, _ = run(comedications=frozenset({"rifampicin"}), comorbidities=frozenset({"active_tb"}))
    assert "efv_plus_ftc_tdf" in ok


def test_abacavir_only_when_tenofovir_unsuitable():
    _, ok, _ = run()
    assert any(f.score <= -30 for f in ok["dtg_abc_3tc"].findings)


def test_osteoporosis_excludes_tenofovir_disoproxil():
    _, ok, ex = run(comorbidities=frozenset({"osteoporosis"}))
    assert "dtg_ftc_tdf" in ex and "dtg_ftc_taf" in ok


def test_pregnancy_uses_the_pregnancy_table():
    report, ok, _ = run(sex="female", pregnancy=Pregnancy.PREGNANT)
    assert report.top.regimen.id == "dtg_ftc_tdf"
    assert ok["dtg_ftc_tdf"].tier_label == "Recommended in pregnancy"
    assert ok["bic_ftc_taf"].tier_label == "Limited pregnancy data"


def test_tier_citations_are_attached():
    report, _, _ = run()
    assert all(a.tier_ref is not None and a.tier_ref.label().startswith("BHIVA") for a in report.recommended)


@needs_smpc
def test_expanded_interactions():
    _, ok, ex = run(comedications=frozenset({"domperidone"}))
    assert "drvc_ftc_taf" in ex and "drvr_ftc_taf" in ex and "dtg_ftc_taf" in ok
    _, ok, _ = run(comedications=frozenset({"voriconazole"}), comorbidities=frozenset({"active_tb"}))
    assert any("300 mg" in d for d in ok["efv_plus_ftc_tdf"].dose_changes)
