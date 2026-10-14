"""Step 3: mode, knowledge-base version, audit trail, hazard log."""
import json
import re

from art_cds import create_app, governance
from art_cds.config import TestConfig
from art_cds.engine.recommender import recommend
from art_cds.knowledge.cases import CASES
from art_cds.safety import HAZARDS, MATRIX

from .conftest import patient


def test_kb_version_format():
    assert re.match(r"^KB-\d{8}-[0-9a-f]{8}$", governance.knowledge_base_version())


def test_audit_records_hash_not_inputs(tmp_path):
    report = recommend(patient())
    ref = governance.audit(report, "education", "test", tmp_path)
    line = json.loads(next(tmp_path.glob("audit-*.jsonl")).read_text().strip())
    assert line["ref"] == ref and len(line["input_sha256"]) == 64 and "inputs" not in line
    assert line["recommended"][0]["regimen"] == report.top.regimen.id
    governance.audit(report, "education", "test", tmp_path, store_inputs=True)
    lines = next(tmp_path.glob("audit-*.jsonl")).read_text().strip().splitlines()
    assert "inputs" in json.loads(lines[-1])


def test_input_digest_is_stable():
    assert governance.input_digest(patient()) == governance.input_digest(patient())
    assert governance.input_digest(patient()) != governance.input_digest(patient(age=36))


def test_education_mode_banner_and_audit_ref(tmp_path):
    class Cfg(TestConfig):
        AUDIT = True
        AUDIT_DIR = str(tmp_path)

    c = create_app(Cfg).test_client()
    html = c.post("/assess", data=CASES[0].as_multidict()).get_data(as_text=True)
    assert "Education mode" in html and "EDUCATIONAL" in html and "Audit ref" in html
    assert list(tmp_path.glob("audit-*.jsonl"))
    assert c.get("/learn/governance").status_code == 200


def test_clinical_mode_hides_education_banner():
    class Cfg(TestConfig):
        MODE = "clinical"

    html = create_app(Cfg).test_client().get("/").get_data(as_text=True)
    assert "Education mode" not in html


def test_hazard_risks_follow_the_matrix():
    assert len(MATRIX) == 5 and all(len(r) == 5 for r in MATRIX)
    assert all(1 <= h.risk <= 5 for h in HAZARDS) and max(h.risk for h in HAZARDS) <= 3
