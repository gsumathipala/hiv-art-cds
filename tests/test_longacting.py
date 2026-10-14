"""Step 5: long-acting module."""
from datetime import date

from art_cds import longacting as la
from art_cds.models import GenotypeTest, TreatmentStatus

from .conftest import run


def test_q2m_schedule_and_windows():
    v = la.cab_rpv_schedule(date(2026, 1, 15), every_2_months=True, visits=4)
    assert [x.target for x in v] == [date(2026, 1, 15), date(2026, 2, 15), date(2026, 4, 15), date(2026, 6, 15)]
    assert v[2].window == (date(2026, 4, 8), date(2026, 4, 22))
    assert "600 mg" in v[3].doses and "900 mg" in v[3].doses


def test_monthly_schedule_doses():
    v = la.cab_rpv_schedule(date(2026, 1, 15), every_2_months=False, visits=3)
    assert "600 mg" in v[0].doses and "400 mg" in v[1].doses


def test_missed_injection_tables():
    assert "resume" in la.missed_injection(date(2026, 1, 1), date(2026, 3, 20), True, 3)[0]
    assert "re-initiate" in la.missed_injection(date(2026, 1, 1), date(2026, 4, 20), True, 3)[0]
    assert "re-initiate" in la.missed_injection(date(2026, 1, 1), date(2026, 3, 20), True, 2)[0]
    assert "continue" in la.missed_injection(date(2026, 1, 1), date(2026, 2, 20), False, 2)[0]


def test_failure_risk():
    assert la.failure_risk(["E138KE", "M184I"], "A6", 32).high
    r = la.failure_risk(["K103N"], "B", 24)
    assert not r.factors and not r.unknown


def test_lenacapavir_schedule():
    v = la.lenacapavir_schedule(date(2026, 3, 2), visits=2)
    assert v[3].target == date(2026, 3, 16) and v[4].target == date(2026, 9, 14)


def test_la_recommendation_flags_risk():
    report, ok, ex = run(status=TreatmentStatus.SUPPRESSED, viral_load=20, prefers_long_acting=True, subtype="A6",
                         height_cm=170, weight_kg=95, genotypes=(GenotypeTest(source="proviral", rt="E138A"),))
    la_assessment = (ok.get("cab_rpv_la") or ex.get("cab_rpv_la"))
    assert any("Two or more baseline risk factors" in f.message for f in la_assessment.findings)


def test_planner_page_and_ics(client):
    html = client.get("/long-acting/?start=2026-01-15&interval=q2m&last=2026-01-01&on=2026-04-20&missed_visit=3"
                      "&drug=cab_rpv").get_data(as_text=True)
    assert "re-initiate" in html and "Download calendar" in html
    r = client.get("/long-acting/schedule.ics?start=2026-01-15&interval=q2m")
    assert r.mimetype == "text/calendar" and b"BEGIN:VEVENT" in r.data
