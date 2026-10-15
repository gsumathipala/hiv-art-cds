"""UK-licensed antiretroviral products and their Summary of Product Characteristics.

Every product maps to one SmPC on the electronic medicines compendium (emc,
https://www.medicines.org.uk/emc). ``tools/fetch_smpc.py`` downloads those SmPCs
and writes a parsed copy to ``art_cds/data/smpc/<key>.json``; the app reads the
parsed copies and never contacts emc at run time.

``emc_id`` pins the exact SmPC and every product sets it, so downloads are reproducible.
Without it the fetcher falls back to searching emc for ``query`` and taking the first result
whose name contains ``match`` — which breaks when emc renames a product (Descovy is listed as
"Emtricitabine/Tenofovir Alafenamide Gilead"). To add a product, find it on
https://www.medicines.org.uk/emc and take the number from its ``/emc/product/<id>/smpc`` URL.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Product:
    key: str
    brand: str
    ingredients: Tuple[str, ...]  # drug codes, see drugs.py
    query: str
    match: str = ""
    emc_id: Optional[int] = None
    route: str = "oral"  # oral | injection
    reference_only: bool = False  # monograph only — not used by the regimen engine

    @property
    def is_combination(self) -> bool:
        return len(self.ingredients) > 1

    @property
    def emc_url(self) -> Optional[str]:
        if self.emc_id is None:
            return None
        return f"https://www.medicines.org.uk/emc/product/{self.emc_id}/smpc"


PRODUCTS: Tuple[Product, ...] = (
    # Integrase-inhibitor based
    Product("biktarvy", "Biktarvy", ("BIC", "FTC", "TAF"), "Biktarvy", "50 mg/200 mg/25 mg", 9313),
    Product("tivicay", "Tivicay", ("DTG",), "Tivicay", "50 mg", 10057),
    Product("dovato", "Dovato", ("DTG", "3TC"), "Dovato", "50 mg/300 mg", 10446),
    Product("triumeq", "Triumeq", ("DTG", "ABC", "3TC"), "Triumeq", "50 mg/600 mg/300 mg", 3318),
    Product("juluca", "Juluca", ("DTG", "RPV"), "Juluca", "50 mg/25 mg", 9246),
    Product("isentress", "Isentress", ("RAL",), "Isentress", "400 mg film-coated", emc_id=6171),
    Product("isentress_600", "Isentress 600 mg", ("RAL",), "Isentress", "600 mg film-coated", emc_id=8436),
    Product("vocabria_tab", "Vocabria tablets", ("CAB",), "Vocabria", "film-coated tablets", emc_id=12958),
    Product("vocabria_inj", "Vocabria injection", ("CAB",), "Vocabria",
            "prolonged-release suspension", emc_id=12957, route="injection"),
    Product("rekambys", "Rekambys", ("RPV",), "Rekambys", "900 mg", 12950, route="injection"),
    # NNRTI based
    Product("pifeltro", "Pifeltro", ("DOR",), "Pifeltro", "100 mg", emc_id=9693),
    Product("delstrigo", "Delstrigo", ("DOR", "3TC", "TDF"), "Delstrigo", "100 mg/300 mg/245 mg", emc_id=9694),
    Product("edurant", "Edurant", ("RPV",), "Edurant", "25 mg film-coated", emc_id=4968),
    Product("odefsey", "Odefsey", ("FTC", "RPV", "TAF"), "Odefsey", "200 mg/25 mg/25 mg", emc_id=7262),
    Product("eviplera", "Eviplera", ("FTC", "RPV", "TDF"), "Eviplera", "200 mg/25 mg/245 mg", 2764),
    Product("efavirenz", "Efavirenz 600 mg (generic)", ("EFV",), "Efavirenz", "600 mg", 13538),
    Product("efv_ftc_tdf", "Efavirenz/emtricitabine/tenofovir disoproxil (generic)",
            ("EFV", "FTC", "TDF"), "Efavirenz", "600 mg/200 mg/245 mg", 9129),
    # Protease-inhibitor based
    Product("symtuza", "Symtuza", ("DRV", "COBI", "FTC", "TAF"), "Symtuza", "800 mg/150 mg/200 mg/10 mg", emc_id=8430),
    Product("rezolsta", "Rezolsta", ("DRV", "COBI"), "Rezolsta", "800 mg/150 mg", 3466),
    Product("prezista", "Prezista 800 mg", ("DRV",), "Prezista", "800 mg film coated", 4993),
    Product("atazanavir", "Atazanavir 300 mg (generic)", ("ATV",), "Atazanavir", "300 mg Capsules", 10779),
    Product("norvir", "Norvir", ("RTV",), "Norvir", "100 mg film-coated", emc_id=510),
    Product("tybost", "Tybost", ("COBI",), "Tybost", "150 mg", emc_id=1277),
    # NRTI backbones and single agents
    Product("descovy", "Descovy", ("FTC", "TAF"), "Descovy", "200 mg/25 mg", emc_id=2108),
    Product("ftc_tdf", "Emtricitabine/tenofovir disoproxil (generic)", ("FTC", "TDF"),
            "Emtricitabine/Tenofovir disoproxil", "200 mg/245 mg", 9028),
    Product("kivexa", "Kivexa", ("ABC", "3TC"), "Kivexa", "600 mg/300 mg", emc_id=3881),
    Product("combivir", "Combivir", ("AZT", "3TC"), "Combivir", "150 mg/300 mg", emc_id=935),
    Product("viread", "Viread", ("TDF",), "Viread", "245 mg", emc_id=1615),
    Product("emtriva", "Emtriva", ("FTC",), "Emtriva", "200 mg hard capsules", emc_id=18),
    Product("epivir", "Epivir", ("3TC",), "Epivir", "300 mg film-coated", emc_id=943),
    Product("ziagen", "Ziagen", ("ABC",), "Ziagen", "300 mg film-coated", emc_id=5518),
    Product("retrovir", "Retrovir", ("AZT",), "Retrovir", "250mg Capsules", 2211),
    # Agents for multiclass resistance — monographs only
    Product("intelence", "Intelence", ("ETR",), "Intelence", "200mg tablets", 7636, reference_only=True),
    Product("celsentri", "Celsentri", ("MVC",), "Celsentri", "300 mg film-coated", emc_id=11437, reference_only=True),
    Product("rukobia", "Rukobia", ("FTR",), "Rukobia", "600 mg", emc_id=12816, reference_only=True),
    Product("sunlenca_tab", "Sunlenca tablets", ("LEN",), "Sunlenca", "300 mg film coated", 14103,
            reference_only=True),
    Product("sunlenca_inj", "Sunlenca injection", ("LEN",), "Sunlenca", "464 mg solution", 14102,
            route="injection", reference_only=True),
)

PRODUCTS_BY_KEY = {p.key: p for p in PRODUCTS}


def products_containing(code: str) -> Tuple[Product, ...]:
    return tuple(p for p in PRODUCTS if code in p.ingredients)
