"""Step 9: infant post-natal prophylaxis and intrapartum management."""
from art_cds import perinatal


def test_low_risk_infant_gets_two_weeks_zidovudine():
    plan = perinatal.infant_pnp(12, True, True, True, 20)
    assert plan.risk == "low" and plan.regimen == "Zidovudine monotherapy" and plan.duration == "2 weeks"
    assert not plan.criteria_failed and len(plan.criteria_met) == 5


def test_each_unmet_criterion_makes_it_high_risk():
    base = dict(art_started_weeks_before_delivery=12, good_engagement=True, vl_in_last_6_weeks=True,
                all_vl_under_50_in_last_10_weeks=True, delivery_vl=20)
    for field, bad in [("art_started_weeks_before_delivery", 6), ("good_engagement", False),
                       ("vl_in_last_6_weeks", False), ("all_vl_under_50_in_last_10_weeks", False),
                       ("delivery_vl", 400), ("delivery_vl", None)]:
        plan = perinatal.infant_pnp(**{**base, field: bad})
        assert plan.risk == "high" and "nevirapine" in plan.regimen, field


def test_nnrti_resistance_warns_about_nevirapine():
    plan = perinatal.infant_pnp(2, False, False, False, 5000, maternal_nnrti_resistance=True)
    assert any("nevirapine will not be effective" in n for n in plan.notes)


def test_breastfeeding_does_not_extend_low_risk_pnp():
    plan = perinatal.infant_pnp(12, True, True, True, 20, breastfeeding=True)
    assert plan.duration == "2 weeks" and any("not usually extended beyond 2 weeks" in n for n in plan.notes)


def test_intrapartum_zidovudine_thresholds():
    assert "recommended" in perinatal.intrapartum_zidovudine(2000)[0]
    assert "can be considered" in perinatal.intrapartum_zidovudine(300)[0]
    assert "not indicated" in perinatal.intrapartum_zidovudine(30)[0]
    assert "untreated" in perinatal.intrapartum_zidovudine(None, untreated_unknown_vl=True)[0].lower()


def test_perinatal_page(client):
    assert client.get("/perinatal/").status_code == 200
    html = client.get("/perinatal/?go=1&art_weeks=12&engagement=on&vl_6_weeks=on&vl_10_weeks=on"
                      "&delivery_vl=20").get_data(as_text=True)
    assert "Zidovudine monotherapy" in html and "low risk" in html
