"""Step 13: clinic letter, patient leaflet and FHIR import."""
import io
import json

import pytest

from art_cds.fhir import parse_bundle
from art_cds.knowledge.cases import CASES_BY_KEY

BUNDLE = {"resourceType": "Bundle", "entry": [
    {"resource": {"resourceType": "Patient", "birthDate": "1985-04-02", "gender": "female"}},
    {"resource": {"resourceType": "Observation", "code": {"coding": [{"code": "20447-9"}]},
                  "effectiveDateTime": "2026-01-10", "valueQuantity": {"value": 48000}}},
    {"resource": {"resourceType": "Observation", "code": {"text": "HIV 1 RNA"}, "effectiveDateTime": "2026-06-01",
                  "valueQuantity": {"value": 50, "comparator": "<"}}},
    {"resource": {"resourceType": "Observation", "code": {"coding": [{"code": "24467-3"}]},
                  "effectiveDateTime": "2026-06-01", "valueQuantity": {"value": 520}}},
    {"resource": {"resourceType": "Observation", "code": {"coding": [{"code": "2160-0"}]},
                  "effectiveDateTime": "2026-06-01", "valueQuantity": {"value": 92}}},
    {"resource": {"resourceType": "Observation", "code": {"text": "Hepatitis B surface antigen"},
                  "valueCodeableConcept": {"text": "Negative"}}},
    {"resource": {"resourceType": "Condition", "code": {"text": "Osteoporosis"}}},
    {"resource": {"resourceType": "MedicationStatement", "status": "active",
                  "medicationCodeableConcept": {"text": "Omeprazole 20mg capsules"}}}]}


def test_bundle_fields_and_notes():
    fields, notes = parse_bundle(BUNDLE)
    assert fields["sex"] == "female" and fields["age"] >= 40
    assert fields["hbsag"] == "negative" and fields["creatinine_umol"] == 92
    assert fields["vl_history"].splitlines() == ["2026-01-10 48000", "2026-06-01 <50"]
    assert fields["cd4"] == 520 and fields["comorbidities"] == ["osteoporosis"]
    assert "omeprazole" in fields["medicines_text"]
    assert any("HLA-B*57:01" in m for _, m in notes)


def test_bundle_rejects_other_json():
    with pytest.raises(ValueError):
        parse_bundle({"resourceType": "Patient"})


def test_import_prefills_the_form(client):
    data = {"bundle": (io.BytesIO(json.dumps(BUNDLE).encode()), "b.json")}
    r = client.post("/assess/import", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'value="92.0"' in html or 'value="92"' in html
    assert "2026-06-01 &lt;50" in html and "Resources read" in html


def test_import_rejects_rubbish(client):
    r = client.post("/assess/import", data={"bundle_text": "not json"})
    assert r.status_code == 422 and "Could not read the bundle" in r.get_data(as_text=True)


def test_clinic_letter(client):
    r = client.post("/assess/letter", data=CASES_BY_KEY["hbv-ckd"].as_multidict())
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Antiretroviral therapy review" in html and "Recommended regimen" in html
    assert "Monitoring plan" in html and "knowledge base" in html


def test_patient_leaflet_shows_tablets_and_side_effects(client):
    r = client.post("/assess/leaflet", data=CASES_BY_KEY["first-line"].as_multidict())
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Your HIV treatment" in html and "<svg" in html
    assert "Possible side effects" in html and "cannot pass HIV on" in html


def test_outputs_reject_invalid_input(client):
    assert client.post("/assess/letter", data={"age": "abc"}).status_code == 422
    assert client.post("/assess/leaflet", data={"age": "abc"}).status_code == 422
