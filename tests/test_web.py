import pytest

from art_cds.knowledge.cases import CASES
from art_cds.knowledge.drugs import CLASSES, DRUGS
from art_cds.knowledge.products import PRODUCTS

PAGES = (["/", "/assess", "/learn/", "/learn/formulary", "/learn/regimens", "/learn/interactions",
          "/learn/resistance", "/learn/cases", "/learn/about"]
         + [f"/learn/class/{c}" for c in CLASSES]
         + [f"/learn/drug/{d}" for d in DRUGS]
         + [f"/learn/product/{p.key}" for p in PRODUCTS]
         + [f"/assess?case={c.key}" for c in CASES])


@pytest.mark.parametrize("url", PAGES)
def test_pages_render(client, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.key)
def test_cases_produce_a_report(client, case):
    r = client.post("/assess", data=case.as_multidict())
    assert r.status_code == 200
    assert b"Regimen recommendation" in r.data and case.learning_points[0][:30].encode() in r.data


def test_invalid_form_is_rejected(client):
    r = client.post("/assess", data={"age": "abc"})
    assert r.status_code == 422 and b"must be a number" in r.data


def test_unknown_case_is_404(client):
    assert client.get("/assess?case=nope").status_code == 404


def test_api(client):
    r = client.post("/api/assess", json={"age": 40, "hbsag": "negative", "hla_b5701": "negative",
                                         "viral_load": 20000, "cd4": 400, "crcl": 100, "genotype_available": True})
    assert r.status_code == 200
    body = r.get_json()
    assert body["recommended"] and {"regimen", "tier", "score", "findings"} <= set(body["recommended"][0])
    assert client.post("/api/assess", json={"age": "x"}).status_code == 422
    assert client.post("/api/assess", data="not json").status_code == 400
