"""Step 4: calculators."""
import json
from pathlib import Path

import pytest

from art_cds import calculators as calc
from art_cds.engine.recommender import derive, recommend
from art_cds.models import ChildPugh

from .conftest import patient

REFERENCE = json.loads((Path(__file__).parent / "data" / "qrisk3_reference.json").read_text())["cases"]


@pytest.mark.parametrize("case", REFERENCE, ids=lambda c: f"{'F' if c['female'] else 'M'}{c['age']}-{c['expected']}")
def test_qrisk3_matches_clinrisk_reference(case):
    expected = case.pop("expected")
    try:
        assert round(calc.qrisk3(calc.QriskInputs(**case)), 1) == expected
    finally:
        case["expected"] = expected


def test_ckd_epi_and_cockcroft_gault():
    assert round(calc.egfr_creatinine_2021(88.42, 50, True), 1) == 68.6
    assert round(calc.egfr_creatinine_2021(88.42, 50, False), 1) == 91.7
    assert round(calc.cockcroft_gault(60, 70, False, 100), 1) == 68.9
    k = calc.kidney(50, False, 80, 150, 0.9)
    assert k.crcl and k.egfr_cr and k.egfr_cys and k.egfr_combined


def test_child_pugh_classes():
    assert calc.child_pugh(20, 40, 1.0, "none", "none") == (5, "A")
    assert calc.child_pugh(40, 30, 1.8, "mild", "none")[1] == "B"
    assert calc.child_pugh(60, 25, 2.5, "severe", "severe") == (15, "C")


def test_derive_uses_calculators():
    d = derive(patient(crcl=None, creatinine_umol=250, weight_kg=70, age=60,
                       bilirubin_umol=60, albumin_g_l=25, inr=2.5, ascites="severe", encephalopathy="mild"))
    assert 25 < d.crcl < 35 and d.child_pugh is ChildPugh.C


def test_frax_and_qrisk_drive_rules():
    report = recommend(patient(frax_mof=7.0))
    assert any(a.regimen.id == "dtg_ftc_tdf" for a in report.excluded)
    report = recommend(patient(qrisk3=14.0))
    abc = next(a for a in report.recommended + report.excluded if a.regimen.id == "dtg_abc_3tc")
    assert any("myocardial infarction" in f.message for f in abc.findings)


def test_calculators_page(client):
    assert client.get("/calculators/").status_code == 200
    html = client.get("/calculators/?calc=kidney&age=50&sex=female&weight=70&creatinine=88.42").get_data(as_text=True)
    assert "68." in html
    html = client.get("/calculators/?calc=qrisk3&age=64&sex=female&ethnicity=2&smoking=0&height=178&weight=80"
                      "&ratio=4&sbp=180&sbp_sd=20").get_data(as_text=True)
    assert "17.2%" in html and "ClinRisk" in html
