"""Complete regimens as prescribed in the UK — which products the patient takes.

Dosing text paraphrases SmPC §4.2 of the listed products; the monograph pages
show the SmPC wording itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .drugs import BOOSTERS, NRTI, drug_class


@dataclass(frozen=True)
class Regimen:
    id: str
    short: str
    components: Tuple[str, ...]  # drug codes, boosters included
    products: Tuple[str, ...]  # product keys the patient takes
    anchor: str
    dosing: str
    units_per_day: float  # tablets/capsules a day (0 for injectables)
    food: str = "With or without food"
    dual: bool = False
    switch_only: bool = False
    long_acting: bool = False

    @property
    def single_tablet(self) -> bool:
        return len(self.products) == 1 and self.units_per_day == 1

    @property
    def core_agents(self) -> Tuple[str, ...]:
        """Non-NRTI, non-booster drugs — the 'third agent(s)'."""
        return tuple(c for c in self.components if c not in BOOSTERS and drug_class(c) != NRTI)

    @property
    def nrtis(self) -> Tuple[str, ...]:
        return tuple(c for c in self.components if drug_class(c) == NRTI)

    @property
    def boosted(self) -> bool:
        return any(c in BOOSTERS for c in self.components)

    @property
    def twice_daily(self) -> bool:
        return "twice daily" in self.dosing


REGIMENS: Tuple[Regimen, ...] = (
    Regimen("bic_ftc_taf", "BIC/FTC/TAF", ("BIC", "FTC", "TAF"), ("biktarvy",), "BIC",
            "Biktarvy 50/200/25 mg — one tablet once daily", 1),
    Regimen("dtg_3tc", "DTG/3TC", ("DTG", "3TC"), ("dovato",), "DTG",
            "Dovato 50/300 mg — one tablet once daily", 1, dual=True),
    Regimen("dtg_ftc_taf", "DTG + FTC/TAF", ("DTG", "FTC", "TAF"), ("tivicay", "descovy"), "DTG",
            "Tivicay 50 mg once daily + Descovy 200/25 mg once daily", 2),
    Regimen("dtg_ftc_tdf", "DTG + FTC/TDF", ("DTG", "FTC", "TDF"), ("tivicay", "ftc_tdf"), "DTG",
            "Tivicay 50 mg once daily + emtricitabine/tenofovir disoproxil 200/245 mg once daily", 2,
            food="FTC/TDF preferably with food"),
    Regimen("dtg_abc_3tc", "DTG/ABC/3TC", ("DTG", "ABC", "3TC"), ("triumeq",), "DTG",
            "Triumeq 50/600/300 mg — one tablet once daily", 1),
    Regimen("drvc_ftc_taf", "DRV/c/FTC/TAF", ("DRV", "COBI", "FTC", "TAF"), ("symtuza",), "DRV",
            "Symtuza 800/150/200/10 mg — one tablet once daily with food", 1, food="With food"),
    Regimen("drvc_ftc_tdf", "DRV/c + FTC/TDF", ("DRV", "COBI", "FTC", "TDF"), ("rezolsta", "ftc_tdf"), "DRV",
            "Rezolsta 800/150 mg once daily with food + emtricitabine/tenofovir disoproxil once daily", 2,
            food="With food"),
    Regimen("drvr_ftc_taf", "DRV/r + FTC/TAF", ("DRV", "RTV", "FTC", "TAF"), ("prezista", "norvir", "descovy"),
            "DRV", "Prezista 800 mg + Norvir 100 mg once daily with food + Descovy 200/10 mg once daily", 3,
            food="With food"),
    Regimen("drvr_ftc_tdf", "DRV/r + FTC/TDF", ("DRV", "RTV", "FTC", "TDF"), ("prezista", "norvir", "ftc_tdf"),
            "DRV", "Prezista 800 mg + Norvir 100 mg once daily with food + emtricitabine/tenofovir disoproxil "
            "once daily", 3, food="With food"),
    Regimen("atvr_ftc_tdf", "ATV/r + FTC/TDF", ("ATV", "RTV", "FTC", "TDF"), ("atazanavir", "norvir", "ftc_tdf"),
            "ATV", "Atazanavir 300 mg + Norvir 100 mg once daily with food + emtricitabine/tenofovir disoproxil "
            "once daily", 3, food="With food"),
    Regimen("ral_ftc_taf", "RAL + FTC/TAF", ("RAL", "FTC", "TAF"), ("isentress_600", "descovy"), "RAL",
            "Isentress 1,200 mg (2 × 600 mg) once daily + Descovy 200/25 mg once daily", 3),
    Regimen("ral_ftc_tdf", "RAL + FTC/TDF", ("RAL", "FTC", "TDF"), ("isentress_600", "ftc_tdf"), "RAL",
            "Isentress 1,200 mg (2 × 600 mg) once daily + emtricitabine/tenofovir disoproxil once daily", 3),
    Regimen("dor_3tc_tdf", "DOR/3TC/TDF", ("DOR", "3TC", "TDF"), ("delstrigo",), "DOR",
            "Delstrigo 100/300/245 mg — one tablet once daily", 1),
    Regimen("dor_ftc_taf", "DOR + FTC/TAF", ("DOR", "FTC", "TAF"), ("pifeltro", "descovy"), "DOR",
            "Pifeltro 100 mg once daily + Descovy 200/25 mg once daily", 2),
    Regimen("rpv_ftc_taf", "RPV/FTC/TAF", ("RPV", "FTC", "TAF"), ("odefsey",), "RPV",
            "Odefsey 200/25/25 mg — one tablet once daily with food", 1, food="With a meal"),
    Regimen("rpv_ftc_tdf", "RPV/FTC/TDF", ("RPV", "FTC", "TDF"), ("eviplera",), "RPV",
            "Eviplera 200/25/245 mg — one tablet once daily with food", 1, food="With a meal"),
    Regimen("efv_ftc_tdf", "EFV/FTC/TDF", ("EFV", "FTC", "TDF"), ("efv_ftc_tdf",), "EFV",
            "Efavirenz/emtricitabine/tenofovir disoproxil 600/200/245 mg — one tablet once daily on an empty "
            "stomach, preferably at bedtime", 1, food="Empty stomach, at bedtime"),
    Regimen("efv_plus_ftc_tdf", "EFV + FTC/TDF", ("EFV", "FTC", "TDF"), ("efavirenz", "ftc_tdf"), "EFV",
            "Efavirenz 600 mg at bedtime on an empty stomach + emtricitabine/tenofovir disoproxil once daily", 2,
            food="Efavirenz on an empty stomach, at bedtime"),
    Regimen("dtg_rpv", "DTG/RPV", ("DTG", "RPV"), ("juluca",), "DTG",
            "Juluca 50/25 mg — one tablet once daily with a meal", 1, food="With a meal", dual=True,
            switch_only=True),
    Regimen("cab_rpv_la", "CAB + RPV long-acting", ("CAB", "RPV"), ("vocabria_inj", "rekambys"), "CAB",
            "Vocabria 600 mg + Rekambys 900 mg IM (gluteal) at month 1 and 2, then every 2 months — or "
            "400 mg + 600 mg monthly after initiation; optional oral lead-in with Vocabria 30 mg + Edurant 25 mg",
            0, food="Not applicable (injection)", dual=True, switch_only=True, long_acting=True),
    Regimen("drvr_dtg", "DRV/r + DTG", ("DRV", "RTV", "DTG"), ("prezista", "norvir", "tivicay"), "DRV",
            "Prezista 800 mg + Norvir 100 mg once daily with food + Tivicay 50 mg once daily "
            "(twice daily dosing where resistance requires it)", 3, food="With food", dual=True),
    Regimen("dtg_azt_3tc", "DTG + AZT/3TC", ("DTG", "AZT", "3TC"), ("tivicay", "combivir"), "DTG",
            "Tivicay 50 mg once daily + Combivir 300/150 mg twice daily", 3),
)

REGIMENS_BY_ID: Dict[str, Regimen] = {r.id: r for r in REGIMENS}
