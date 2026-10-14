"""Step 6: medicines reconciliation."""
from art_cds.engine.recommender import recommend
from art_cds.knowledge.interactions import COMEDICATIONS_BY_KEY
from art_cds.knowledge.medicines import SYNONYMS, reconcile

from .conftest import patient


def test_every_synonym_targets_a_known_comedication():
    assert set(SYNONYMS) == set(COMEDICATIONS_BY_KEY)


def test_brands_doses_typos_and_combinations():
    r = {x.text: x for x in reconcile("Omeprazole 20mg OD\nSeretide 250 inhaler\natorvastain 40 mg\nlevothyroxine")}
    assert r["Omeprazole 20mg OD"].key == "ppi"
    assert r["Seretide 250 inhaler"].key == "inhaled_steroid" and r["Seretide 250 inhaler"].also == ("salmeterol",)
    assert r["atorvastain 40 mg"].key == "atorvastatin" and r["atorvastain 40 mg"].fuzzy
    assert r["levothyroxine"].key is None


def test_free_text_drives_interactions_and_flags_unknowns():
    report = recommend(patient(medicines_text="Tegretol 200mg bd\nlevothyroxine 100 micrograms"))
    assert "carbamazepine" in report.patient.comedications
    assert any(a.regimen.id == "dor_3tc_tdf" for a in report.excluded)
    assert any("levothyroxine" in a.message for a in report.alerts)
