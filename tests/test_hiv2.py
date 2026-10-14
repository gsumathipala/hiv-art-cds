"""Step 7: HIV-2 and dual infection."""
from .conftest import run


def test_hiv2_excludes_nnrtis_and_disables_hiv1_scoring():
    report, ok, ex = run(virus_type="HIV-2", rt_mutations="K103N")
    assert "dor_3tc_tdf" in ex and "efv_plus_ftc_tdf" in ex
    assert report.resistance is None
    assert any("HIV-2 expert" in a.message for a in report.alerts)
    dtg = ok["dtg_ftc_tdf"]
    assert any("twice daily" in d for d in dtg.dose_changes)
    assert ok["dtg_3tc"].score < ok["dtg_ftc_tdf"].score


def test_dual_infection_keeps_hiv1_resistance():
    report, _, ex = run(virus_type="HIV-1/HIV-2", rt_mutations="M184V")
    assert report.resistance is not None and "dor_3tc_tdf" in ex
