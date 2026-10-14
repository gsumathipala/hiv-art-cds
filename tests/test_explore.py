"""Step 11: interactive resistance and pharmacokinetic visuals."""
import pytest

from art_cds.visuals import pharmacokinetics as pk


def test_resistance_explorer_updates_activity(client):
    plain = client.get("/explore/resistance").get_data(as_text=True)
    assert "Susceptible" in plain
    html = client.get("/explore/resistance?rt=M184V+K65R").get_data(as_text=True)
    assert "High-level resistance" in html
    assert "reduces viral fitness" in html  # M184V teaching note shown
    assert "0.00" in html  # GSS contribution for a drug with no activity


def test_resistance_explorer_reports_bad_input(client):
    html = client.get("/explore/resistance?rt=X999Q").get_data(as_text=True)
    assert "Not valid notation" in html


@pytest.mark.parametrize("profile", pk.PROFILES, ids=lambda p: p.code)
def test_every_curve_renders(client, profile):
    svg = pk.curve(profile.code)
    assert svg.startswith("<svg") and "<path" in svg
    assert client.get(f"/explore/pharmacokinetics?drug={profile.code}").status_code == 200


def test_curve_tail_is_shown_when_dosing_stops():
    assert "declining tail" in pk.curve("CAB-LA", doses_count=4, stop_after=2)
    assert "declining tail" not in pk.curve("CAB-LA", doses_count=4)


def test_concentration_accumulates_then_falls():
    p = pk.PROFILES_BY_CODE["DTG"]
    doses = [i * 24 for i in range(5)]
    assert pk._concentration(96, p, doses) > pk._concentration(24, p, doses)  # accumulation
    assert pk._concentration(400, p, doses) < pk._concentration(96, p, doses)  # washout


def test_unknown_drug_falls_back(client):
    assert client.get("/explore/pharmacokinetics?drug=NOPE").status_code == 200
