from art_cds.engine.resistance import interpret, parse, regimen_gss


def test_parse_handles_mixtures_prefixes_and_insertions():
    found, bad = parse("K103KN, rt:M184VI T69ins X999Q", "RT")
    assert found == ["K103N", "M184V", "M184I", "T69ins"]
    assert bad == ["X999Q"]


def test_k65r_m184v_profile():
    r = interpret(rt="K65R M184V")
    assert r.level("3TC") == 5
    assert r.level("TDF") == 4 and r.level("TAF") == 4  # TAF scored as tenofovir
    assert r.level("AZT") == 1  # hypersusceptible


def test_integrase_combination_penalty():
    r = interpret(integrase="G140S Q148H")
    assert r.level("RAL") == 5
    assert r.level("DTG") == 4
    assert "(G140S + Q148H)" in r.get("DTG").contributors


def test_k103n_spares_second_generation_nnrtis():
    r = interpret(rt="K103N")
    assert r.level("EFV") == 5
    assert r.level("RPV") == 1 and r.level("DOR") == 1


def test_gss_ignores_boosters():
    r = interpret(rt="M184V")
    assert regimen_gss(("DRV", "RTV", "FTC", "TAF"), r) == 2.0
    assert regimen_gss(("DTG",), None) is None
