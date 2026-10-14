"""Step 12: SmPC change monitoring."""
import copy
import json
from pathlib import Path

from art_cds.knowledge import smpc
from tools import check_updates


def _doc(key="biktarvy"):
    return json.loads((Path(smpc.DATA) / f"{key}.json").read_text(encoding="utf-8"))


def test_no_difference_for_identical_documents():
    doc = _doc()
    assert check_updates.compare(doc, copy.deepcopy(doc)) == []


def test_detects_a_changed_watched_section():
    old = _doc()
    new = copy.deepcopy(old)
    new["sections"]["contraindications"]["blocks"].append({"type": "p", "text": "Concomitant use with example drug."})
    changed = check_updates.compare(old, new)
    assert changed and changed[0][0] == "contraindications" and changed[0][1] == 1


def test_ignores_sections_that_are_not_watched():
    old = _doc()
    new = copy.deepcopy(old)
    new["sections"].setdefault("storage", {"number": "6.4", "title": "Storage", "blocks": []})
    new["sections"]["storage"]["blocks"] = [{"type": "p", "text": "Store below 30 C."}]
    assert check_updates.compare(old, new) == []


def test_quick_mode_reverifies_without_network(capsys):
    assert check_updates.main(["--quick"]) == 0
    assert "claims verified" in capsys.readouterr().out
