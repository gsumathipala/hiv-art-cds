"""Step 2: viral-load course classification and the longitudinal record."""
from art_cds.engine.recommender import derive, recommend
from art_cds.engine.virology import classify
from art_cds.models import ArtEpisode, LabValue, TreatmentStatus
from art_cds.web.forms import parse_patient

from .conftest import patient


def vl(*pairs):
    return tuple(LabValue(d, float(v.strip("<")), v.startswith("<")) for d, v in pairs)


def test_blip_is_flanked_by_undetectable_results():
    a = classify(vl(("2024-01-01", "<50"), ("2024-04-01", "120"), ("2024-07-01", "<50")))
    assert a.status == "undetectable" and a.blips == 1


def test_low_level_viraemia_and_confirmed_failure():
    assert classify(vl(("2024-01-01", "<50"), ("2024-04-01", "120"), ("2024-07-01", "180"))).status == \
        "low-level viraemia"
    assert classify(vl(("2024-01-01", "<50"), ("2024-04-01", "900"), ("2024-05-01", "3000"))).status == \
        "confirmed virological failure"
    assert classify(vl(("2024-01-01", "<50"), ("2024-04-01", "900"))).status == "suspected virological failure"


def test_results_before_art_start_are_ignored():
    a = classify(vl(("2024-01-01", "90000"), ("2024-04-01", "<50")), (ArtEpisode(start="2024-02-01"),))
    assert a.status == "undetectable" and len(a.labels) == 1


def test_derive_fills_current_values_and_failed_classes():
    p = patient(status=TreatmentStatus.FAILURE, viral_load=None, cd4=None,
                vl_history=vl(("2025-01-01", "15000")), cd4_history=vl(("2025-01-01", "210")),
                art_history=(ArtEpisode(start="2019-01-01", stop="2025-02-01", components=("EFV", "FTC", "TDF"),
                                        reason_stopped="virological failure"),))
    d = derive(p)
    assert d.viral_load == 15000 and d.cd4 == 210 and d.failed_classes == {"NNRTI", "NRTI"}


def test_repeated_blips_steer_away_from_low_barrier_switches():
    p = patient(status=TreatmentStatus.SUPPRESSED, viral_load=20,
                vl_history=vl(("2023-01-01", "<50"), ("2023-04-01", "90"), ("2023-07-01", "<50"),
                              ("2023-10-01", "150"), ("2024-01-01", "<50")))
    report = recommend(p)
    rpv = next(a for a in report.recommended + report.excluded if a.regimen.id == "rpv_ftc_taf")
    assert any("high genetic-barrier" in f.message for f in rpv.findings)


def test_form_parses_history_lines_and_errors():
    p, e = parse_patient({"age": 40, "vl_history": "2025-01-01 <50\n2025-06-01 TND",
                          "art_history": [{"start": "2025-01-01", "other": "Biktarvy"}]})
    assert not e and p.vl_history[1].censored and p.art_history[0].components == ("BIC", "FTC", "TAF")
    _, e = parse_patient({"age": 40, "vl_history": "yesterday 400"})
    assert "vl_history" in e
