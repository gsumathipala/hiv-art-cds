"""The knowledge base must agree with the UK SmPC text it cites."""
from art_cds.knowledge import smpc
from art_cds.knowledge.products import PRODUCTS
from art_cds.visuals import pills
from art_cds.verification import check

from .conftest import needs_smpc


@needs_smpc
def test_every_claim_is_supported_by_its_smpc_or_guideline():
    failures, missing, total = check()
    assert total > 200
    assert not failures, failures
    assert not missing, missing


@needs_smpc
def test_every_product_has_an_smpc_with_appearance_and_adverse_reactions():
    for p in PRODUCTS:
        doc = smpc.load(p.key)
        assert doc is not None, p.key
        assert pills.units_for(p.key), f"{p.key}: no dose unit parsed from §3"
        assert smpc.adverse_grid(p.key), f"{p.key}: no adverse reactions parsed from §4.8"


def test_pill_parser_reads_colour_shape_size_and_debossing():
    text = ("Purplish-brown, capsule-shaped, film-coated tablet debossed with “GSI” on one side and “9883” on the "
            "other side of the tablet. Each tablet is approximately 15 mm × 8 mm.")
    (unit,) = pills.parse_units(text)
    assert (unit.colour_word, unit.shape, unit.length_mm, unit.width_mm) == ("purplish-brown", "capsule", 15, 8)
    assert unit.deboss == ("GSI", "9883")
    assert "<svg" in pills.svg_for(unit)


def test_pill_parser_reads_two_tone_capsules_and_ignores_ink():
    (unit,) = pills.parse_units("Each capsule has a white opaque body with a light blue opaque cap, of dimensions "
                                "19.4 mm x 6.9 mm. Each capsule is printed with “200 mg” on the cap in black ink.")
    assert unit.kind == "hardcap" and unit.colour_word == "white" and unit.cap_colour == pills.COLOURS["light blue"]
