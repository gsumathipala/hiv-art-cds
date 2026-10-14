"""Clinically important interactions between antiretrovirals and co-medications.

Every entry cites the UK SmPC section it comes from and carries ``evidence`` —
regular expressions that must all occur in that section. ``tools/verify_smpc.py``
and the test suite check each entry against the downloaded SmPCs, so an entry
the SmPC does not support fails the build.

Severity:
  contraindicated — SmPC §4.3 contraindication (regimen excluded)
  avoid           — SmPC says not recommended / should be avoided
  adjust          — co-administration needs a dose or timing change
  monitor         — usable with monitoring
For anything not listed, check the Liverpool HIV Drug Interactions checker
(https://www.hiv-druginteractions.org).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

CONTRAINDICATED = "contraindicated"
AVOID = "avoid"
ADJUST = "adjust"
MONITOR = "monitor"

SEVERITY_ORDER = {CONTRAINDICATED: 0, AVOID: 1, ADJUST: 2, MONITOR: 3}


@dataclass(frozen=True)
class Comedication:
    key: str
    label: str
    group: str


COMEDICATIONS: Tuple[Comedication, ...] = (
    Comedication("rifampicin", "Rifampicin", "Antimycobacterials"),
    Comedication("rifabutin", "Rifabutin", "Antimycobacterials"),
    Comedication("carbamazepine", "Carbamazepine", "Anticonvulsants"),
    Comedication("oxcarbazepine", "Oxcarbazepine", "Anticonvulsants"),
    Comedication("phenytoin", "Phenytoin / fosphenytoin", "Anticonvulsants"),
    Comedication("phenobarbital", "Phenobarbital / primidone", "Anticonvulsants"),
    Comedication("st_johns_wort", "St John's wort", "Herbal"),
    Comedication("ppi", "Proton pump inhibitor (e.g. omeprazole)", "Gastrointestinal"),
    Comedication("h2ra", "H2-receptor antagonist (e.g. famotidine)", "Gastrointestinal"),
    Comedication("antacids", "Antacids / polyvalent cations (Al, Mg, Ca, Fe, Zn)", "Gastrointestinal"),
    Comedication("simvastatin", "Simvastatin or lovastatin", "Cardiovascular"),
    Comedication("atorvastatin", "Atorvastatin or rosuvastatin", "Cardiovascular"),
    Comedication("amiodarone", "Amiodarone", "Cardiovascular"),
    Comedication("fampridine", "Fampridine (Fampyra)", "CNS"),
    Comedication("doac", "Rivaroxaban / apixaban / dabigatran", "Cardiovascular"),
    Comedication("ticagrelor", "Ticagrelor or clopidogrel", "Cardiovascular"),
    Comedication("metformin", "Metformin", "Endocrine"),
    Comedication("dexamethasone", "Dexamethasone (systemic, more than one dose)", "Endocrine"),
    Comedication("inhaled_steroid", "Fluticasone / budesonide (inhaled or nasal)", "Respiratory"),
    Comedication("salmeterol", "Salmeterol", "Respiratory"),
    Comedication("hormonal_contraception", "Hormonal contraception (oral, implant, patch)", "Reproductive"),
    Comedication("methadone", "Methadone", "Opioid substitution"),
    Comedication("midazolam_oral", "Midazolam (oral) or triazolam", "CNS"),
    Comedication("quetiapine", "Quetiapine", "CNS"),
    Comedication("pimozide", "Pimozide or lurasidone", "CNS"),
    Comedication("sildenafil_pah", "Sildenafil for pulmonary arterial hypertension", "Other"),
    Comedication("colchicine", "Colchicine", "Other"),
    Comedication("ergot", "Ergot derivatives (ergotamine)", "Other"),
    Comedication("sof_vel", "Sofosbuvir/velpatasvir (Epclusa)", "Hepatitis C"),
    Comedication("glec_pib", "Glecaprevir/pibrentasvir (Maviret)", "Hepatitis C"),
    Comedication("elbasvir", "Elbasvir/grazoprevir (Zepatier)", "Hepatitis C"),
    Comedication("ledipasvir", "Ledipasvir/sofosbuvir (Harvoni)", "Hepatitis C"),
    Comedication("rifapentine", "Rifapentine", "Antimycobacterials"),
    Comedication("clarithromycin", "Clarithromycin", "Anti-infectives"),
    Comedication("itraconazole", "Itraconazole or posaconazole", "Anti-infectives"),
    Comedication("voriconazole", "Voriconazole", "Anti-infectives"),
    Comedication("artemether", "Artemether/lumefantrine (Riamet)", "Anti-infectives"),
    Comedication("atovaquone", "Atovaquone/proguanil (Malarone)", "Anti-infectives"),
    Comedication("tacrolimus", "Tacrolimus or ciclosporin", "Immunosuppressants"),
    Comedication("dronedarone", "Dronedarone or ranolazine", "Cardiovascular"),
    Comedication("ivabradine", "Ivabradine", "Cardiovascular"),
    Comedication("digoxin", "Digoxin", "Cardiovascular"),
    Comedication("lomitapide", "Lomitapide", "Cardiovascular"),
    Comedication("domperidone", "Domperidone", "Gastrointestinal"),
    Comedication("naloxegol", "Naloxegol", "Gastrointestinal"),
    Comedication("alfuzosin", "Alfuzosin", "Urology & sexual health"),
    Comedication("pde5_ed", "Sildenafil/tadalafil/vardenafil for erectile dysfunction", "Urology & sexual health"),
    Comedication("avanafil", "Avanafil", "Urology & sexual health"),
    Comedication("lamotrigine", "Lamotrigine", "Anticonvulsants"),
    Comedication("antidepressant", "SSRIs or trazodone", "CNS"),
    Comedication("opioid", "Fentanyl or oxycodone", "Opioid substitution"),
    Comedication("steroid_injection", "Corticosteroid injections (e.g. triamcinolone, methylprednisolone)", "Endocrine"),
    Comedication("bosentan", "Bosentan", "Respiratory"),
)

COMEDICATIONS_BY_KEY = {c.key: c for c in COMEDICATIONS}


@dataclass(frozen=True)
class Interaction:
    comed: str
    drug: str
    severity: str
    message: str
    product: str  # SmPC the statement comes from
    section: str  # "4.3" or "4.5"
    evidence: Tuple[str, ...]  # regexes that must all appear in that section
    dose_change: Optional[str] = None
    oral_only: bool = False  # does not apply to the long-acting injection


_I = Interaction

INTERACTIONS: Tuple[Interaction, ...] = (
    # ---- rifamycins
    _I("rifampicin", "BIC", CONTRAINDICATED, "Rifampicin markedly lowers bictegravir exposure.",
       "biktarvy", "4.3", (r"rifampicin",)),
    _I("rifampicin", "DTG", ADJUST, "Rifampicin lowers dolutegravir exposure; the dose must be doubled.",
       "tivicay", "4.2", (r"rifampicin", r"twice daily"),
       dose_change="Dolutegravir 50 mg twice daily while on rifampicin and for 2 weeks after "
                   "(not with integrase resistance) — with Dovato/Triumeq add a separate Tivicay 50 mg "
                   "dose about 12 hours later"),
    _I("rifampicin", "RAL", ADJUST, "Rifampicin lowers raltegravir exposure (AUC ↓40%); if co-administration is "
       "unavoidable the SmPC says doubling the dose can be considered.",
       "isentress", "4.5", (r"rifampicin", r"doubling of the dose"),
       dose_change="Consider doubling raltegravir to 800 mg twice daily with rifampicin (not the 1,200 mg "
                   "once-daily regimen)"),
    _I("rifampicin", "RPV", CONTRAINDICATED, "Rifampicin markedly lowers rilpivirine exposure.",
       "edurant", "4.3", (r"rifampicin",)),
    _I("rifampicin", "DOR", CONTRAINDICATED, "Strong CYP3A induction by rifampicin markedly lowers doravirine.",
       "pifeltro", "4.3", (r"rifampicin",)),
    _I("rifampicin", "CAB", CONTRAINDICATED, "Rifampicin markedly lowers cabotegravir exposure.",
       "vocabria_tab", "4.3", (r"rifampicin",)),
    _I("rifampicin", "DRV", CONTRAINDICATED, "Rifampicin markedly lowers darunavir exposure.",
       "prezista", "4.3", (r"rifampicin",)),
    _I("rifampicin", "ATV", CONTRAINDICATED, "Rifampicin markedly lowers atazanavir exposure.",
       "atazanavir", "4.3", (r"rifampicin",)),
    _I("rifampicin", "TAF", AVOID, "Rifampicin, a P-gp inducer, lowers tenofovir alafenamide exposure.",
       "descovy", "4.5", (r"rifampicin", r"not recommended")),
    _I("rifampicin", "EFV", MONITOR, "Efavirenz 600 mg can be given with rifampicin (efavirenz exposure falls "
       "modestly; the SmPC allows a dose increase in patients ≥50 kg).",
       "efavirenz", "4.5", (r"rifampicin",)),
    _I("rifabutin", "BIC", AVOID, "Rifabutin lowers bictegravir exposure.",
       "biktarvy", "4.5", (r"rifabutin", r"not recommended")),
    _I("rifabutin", "DOR", ADJUST, "Rifabutin lowers doravirine exposure.",
       "pifeltro", "4.2", (r"rifabutin", r"twice daily"),
       dose_change="Doravirine 100 mg twice daily (about 12 h apart) with rifabutin"),
    _I("rifabutin", "RPV", ADJUST, "Rifabutin lowers rilpivirine exposure.",
       "edurant", "4.2", (r"rifabutin", r"50 mg")),
    _I("rifabutin", "CAB", AVOID, "Rifabutin lowers cabotegravir exposure; concomitant use should be avoided.",
       "vocabria_inj", "4.5", (r"rifabutin", r"should be avoided")),
    _I("rifabutin", "RTV", ADJUST, "Ritonavir-boosted PIs raise rifabutin (and its active metabolite).",
       "prezista", "4.5", (r"rifabutin", r"150 mg")),
    _I("rifabutin", "TAF", AVOID, "Rifabutin lowers tenofovir alafenamide exposure.",
       "descovy", "4.5", (r"rifabutin", r"not recommended")),
    # ---- enzyme-inducing anticonvulsants
    _I("carbamazepine", "BIC", AVOID, "Carbamazepine lowers bictegravir exposure.",
       "biktarvy", "4.5", (r"carbamazepine", r"not recommended")),
    _I("carbamazepine", "DTG", ADJUST, "Carbamazepine lowers dolutegravir exposure.",
       "tivicay", "4.5", (r"carbamazepine", r"twice daily"),
       dose_change="Dolutegravir 50 mg twice daily with carbamazepine (avoid with integrase resistance)"),
    _I("carbamazepine", "RPV", CONTRAINDICATED, "Carbamazepine markedly lowers rilpivirine.",
       "edurant", "4.3", (r"carbamazepine",)),
    _I("carbamazepine", "DOR", CONTRAINDICATED, "Carbamazepine markedly lowers doravirine.",
       "pifeltro", "4.3", (r"carbamazepine",)),
    _I("carbamazepine", "CAB", CONTRAINDICATED, "Carbamazepine markedly lowers cabotegravir.",
       "vocabria_tab", "4.3", (r"carbamazepine",)),
    _I("carbamazepine", "COBI", CONTRAINDICATED, "Carbamazepine lowers cobicistat and the boosted PI.",
       "rezolsta", "4.3", (r"carbamazepine",)),
    _I("carbamazepine", "TAF", AVOID, "Carbamazepine lowers tenofovir alafenamide exposure.",
       "descovy", "4.5", (r"carbamazepine", r"not recommended")),
    _I("oxcarbazepine", "BIC", AVOID, "Oxcarbazepine lowers bictegravir exposure.",
       "biktarvy", "4.5", (r"oxcarbazepine", r"not recommended")),
    _I("oxcarbazepine", "RPV", CONTRAINDICATED, "Oxcarbazepine lowers rilpivirine.",
       "edurant", "4.3", (r"oxcarbazepine",)),
    _I("oxcarbazepine", "DOR", CONTRAINDICATED, "Oxcarbazepine lowers doravirine.",
       "pifeltro", "4.3", (r"oxcarbazepine",)),
    _I("oxcarbazepine", "CAB", CONTRAINDICATED, "Oxcarbazepine lowers cabotegravir.",
       "vocabria_tab", "4.3", (r"oxcarbazepine",)),
    _I("oxcarbazepine", "DTG", AVOID, "Oxcarbazepine lowers dolutegravir exposure.",
       "tivicay", "4.5", (r"oxcarbazepine",)),
    _I("phenytoin", "BIC", AVOID, "Phenytoin lowers bictegravir exposure.",
       "biktarvy", "4.5", (r"phenytoin", r"not recommended")),
    _I("phenytoin", "DTG", AVOID, "Phenytoin lowers dolutegravir exposure.",
       "tivicay", "4.5", (r"phenytoin",)),
    _I("phenytoin", "RPV", CONTRAINDICATED, "Phenytoin lowers rilpivirine.", "edurant", "4.3", (r"phenytoin",)),
    _I("phenytoin", "DOR", CONTRAINDICATED, "Phenytoin lowers doravirine.", "pifeltro", "4.3", (r"phenytoin",)),
    _I("phenytoin", "CAB", CONTRAINDICATED, "Phenytoin lowers cabotegravir.",
       "vocabria_tab", "4.3", (r"phenytoin",)),
    _I("phenytoin", "COBI", CONTRAINDICATED, "Phenytoin lowers cobicistat and the boosted PI.",
       "rezolsta", "4.3", (r"phenytoin",)),
    _I("phenytoin", "TAF", AVOID, "Phenytoin lowers tenofovir alafenamide.",
       "descovy", "4.5", (r"phenytoin", r"not recommended")),
    _I("phenobarbital", "BIC", AVOID, "Phenobarbital lowers bictegravir.",
       "biktarvy", "4.5", (r"phenobarbital", r"not recommended")),
    _I("phenobarbital", "DTG", AVOID, "Phenobarbital lowers dolutegravir.",
       "tivicay", "4.5", (r"phenobarbital",)),
    _I("phenobarbital", "RPV", CONTRAINDICATED, "Phenobarbital lowers rilpivirine.",
       "edurant", "4.3", (r"phenobarbital",)),
    _I("phenobarbital", "DOR", CONTRAINDICATED, "Phenobarbital lowers doravirine.",
       "pifeltro", "4.3", (r"phenobarbital",)),
    _I("phenobarbital", "CAB", CONTRAINDICATED, "Phenobarbital lowers cabotegravir.",
       "vocabria_tab", "4.3", (r"phenobarbital",)),
    _I("phenobarbital", "COBI", CONTRAINDICATED, "Phenobarbital lowers cobicistat and the boosted PI.",
       "rezolsta", "4.3", (r"phenobarbital",)),
    # ---- St John's wort
    _I("st_johns_wort", "BIC", CONTRAINDICATED, "St John's wort induces bictegravir metabolism.",
       "biktarvy", "4.3", (r"st\.? john",)),
    _I("st_johns_wort", "DTG", AVOID, "St John's wort lowers dolutegravir exposure.",
       "tivicay", "4.5", (r"st\.? john",)),
    _I("st_johns_wort", "RPV", CONTRAINDICATED, "St John's wort lowers rilpivirine.",
       "edurant", "4.3", (r"st\.? john",)),
    _I("st_johns_wort", "DOR", CONTRAINDICATED, "St John's wort lowers doravirine.",
       "pifeltro", "4.3", (r"st\.? john",)),
    _I("st_johns_wort", "DRV", CONTRAINDICATED, "St John's wort lowers darunavir.",
       "prezista", "4.3", (r"st\.? john",)),
    _I("st_johns_wort", "ATV", CONTRAINDICATED, "St John's wort lowers atazanavir.",
       "atazanavir", "4.3", (r"st\.? john",)),
    _I("st_johns_wort", "EFV", CONTRAINDICATED, "St John's wort lowers efavirenz.",
       "efavirenz", "4.3", (r"st\.? john",)),
    _I("st_johns_wort", "TAF", AVOID, "St John's wort lowers tenofovir alafenamide.",
       "descovy", "4.5", (r"st\.? john", r"not recommended")),
    # ---- acid-reducing agents and cations
    _I("ppi", "RPV", CONTRAINDICATED, "Proton pump inhibitors raise gastric pH and markedly lower oral "
       "rilpivirine absorption.", "edurant", "4.3", (r"proton pump",), oral_only=True),
    _I("ppi", "ATV", AVOID, "Proton pump inhibitors markedly lower atazanavir absorption.",
       "atazanavir", "4.5", (r"proton pump|omeprazole", r"not recommended")),
    _I("h2ra", "RPV", ADJUST, "H2-receptor antagonists lower oral rilpivirine absorption.",
       "edurant", "4.5", (r"H2", r"12 hours", r"4 hours"),
       dose_change="Give the H2-antagonist ≥12 h before or ≥4 h after rilpivirine", oral_only=True),
    _I("h2ra", "ATV", ADJUST, "H2-receptor antagonists lower atazanavir absorption.",
       "atazanavir", "4.5", (r"H2", r"famotidine")),
    _I("antacids", "BIC", ADJUST, "Polyvalent cations chelate bictegravir.",
       "biktarvy", "4.5", (r"antacid", r"2 hours")),
    _I("antacids", "DTG", ADJUST, "Polyvalent cations chelate dolutegravir.",
       "tivicay", "4.5", (r"antacid", r"2 hours", r"6 hours"),
       dose_change="Take dolutegravir 2 h before or 6 h after antacids/supplements (iron or calcium may be "
                   "taken together with dolutegravir with food)"),
    _I("antacids", "RAL", AVOID, "Aluminium/magnesium antacids chelate raltegravir.",
       "isentress", "4.5", (r"antacid", r"not recommended")),
    _I("antacids", "CAB", ADJUST, "Polyvalent-cation antacids lower oral cabotegravir.",
       "vocabria_tab", "4.5", (r"antacid", r"2 hours", r"4 hours"),
       dose_change="Oral cabotegravir 2 h before or 4 h after antacids", oral_only=True),
    _I("antacids", "RPV", ADJUST, "Antacids lower oral rilpivirine absorption.",
       "edurant", "4.5", (r"antacid", r"2 hours", r"4 hours"),
       dose_change="Antacids ≥2 h before or ≥4 h after rilpivirine", oral_only=True),
    # ---- lipid-lowering, cardiovascular
    _I("simvastatin", "RTV", CONTRAINDICATED, "Ritonavir markedly raises simvastatin/lovastatin "
       "(rhabdomyolysis).", "norvir", "4.3", (r"simvastatin",)),
    _I("simvastatin", "COBI", CONTRAINDICATED, "Cobicistat markedly raises simvastatin/lovastatin.",
       "rezolsta", "4.3", (r"simvastatin",)),
    _I("atorvastatin", "COBI", ADJUST, "Boosted darunavir raises atorvastatin/rosuvastatin.",
       "rezolsta", "4.5", (r"atorvastatin", r"rosuvastatin"),
       dose_change="Start atorvastatin at 10 mg and titrate; use the lowest effective rosuvastatin dose"),
    _I("atorvastatin", "RTV", ADJUST, "Boosted darunavir raises atorvastatin/rosuvastatin.",
       "prezista", "4.5", (r"atorvastatin", r"rosuvastatin"),
       dose_change="Start atorvastatin at 10 mg and titrate; use the lowest effective rosuvastatin dose"),
    _I("amiodarone", "RTV", CONTRAINDICATED, "Ritonavir raises amiodarone (arrhythmia risk).",
       "norvir", "4.3", (r"amiodarone",)),
    _I("amiodarone", "COBI", AVOID, "Cobicistat raises amiodarone.",
       "rezolsta", "4.5", (r"amiodarone",)),
    _I("fampridine", "DTG", CONTRAINDICATED, "Dolutegravir inhibits OCT2 and raises fampridine (seizure risk) — "
       "narrow-therapeutic-index OCT2 substrates are contraindicated.", "tivicay", "4.3", (r"fampridine",)),
    _I("doac", "COBI", AVOID, "Cobicistat raises rivaroxaban/apixaban/dabigatran exposure (bleeding).",
       "rezolsta", "4.5", (r"rivaroxaban",)),
    _I("doac", "RTV", AVOID, "Ritonavir-boosted darunavir raises rivaroxaban/apixaban (bleeding).",
       "prezista", "4.5", (r"rivaroxaban",)),
    _I("ticagrelor", "COBI", CONTRAINDICATED, "Boosting raises ticagrelor; clopidogrel activation is reduced.",
       "rezolsta", "4.3", (r"ticagrelor",)),
    _I("ticagrelor", "RTV", AVOID, "Ritonavir-boosted darunavir raises ticagrelor and reduces clopidogrel "
       "activation.", "prezista", "4.5", (r"ticagrelor",)),
    # ---- endocrine
    _I("metformin", "DTG", ADJUST, "Dolutegravir raises metformin (OCT2/MATE1 inhibition).",
       "tivicay", "4.5", (r"metformin",),
       dose_change="Consider a metformin dose adjustment when starting or stopping dolutegravir; monitor renal "
                   "function"),
    _I("metformin", "BIC", MONITOR, "Bictegravir raises metformin exposure.",
       "biktarvy", "4.5", (r"metformin",)),
    _I("dexamethasone", "RPV", CONTRAINDICATED, "Systemic dexamethasone (more than a single dose) lowers "
       "rilpivirine.", "edurant", "4.3", (r"dexamethasone",)),
    _I("inhaled_steroid", "RTV", AVOID, "Ritonavir raises fluticasone/budesonide — Cushing's syndrome and "
       "adrenal suppression reported.", "norvir", "4.5", (r"fluticasone",)),
    _I("inhaled_steroid", "COBI", AVOID, "Cobicistat raises fluticasone/budesonide (Cushing's syndrome).",
       "rezolsta", "4.5", (r"fluticasone|budesonide",)),
    _I("salmeterol", "RTV", AVOID, "Ritonavir raises salmeterol (QT prolongation, palpitations).",
       "norvir", "4.5", (r"salmeterol",)),
    _I("salmeterol", "COBI", AVOID, "Cobicistat raises salmeterol.",
       "rezolsta", "4.5", (r"salmeterol",)),
    # ---- contraception, opioid substitution
    _I("hormonal_contraception", "EFV", AVOID, "Efavirenz lowers etonogestrel and levonorgestrel — implant and "
       "progestogen-only methods may fail.", "efavirenz", "4.5", (r"etonogestrel|levonorgestrel",)),
    _I("hormonal_contraception", "RTV", ADJUST, "Ritonavir-boosted darunavir lowers ethinylestradiol.",
       "prezista", "4.5", (r"ethinylestradiol",),
       dose_change="Use an additional or alternative (non-hormonal) contraceptive method"),
    _I("hormonal_contraception", "COBI", MONITOR, "Cobicistat-boosted darunavir alters ethinylestradiol and "
       "drospirenone exposure.", "rezolsta", "4.5", (r"drospirenone",)),
    _I("methadone", "EFV", ADJUST, "Efavirenz lowers methadone — withdrawal symptoms.",
       "efavirenz", "4.5", (r"methadone",),
       dose_change="Monitor for opioid withdrawal; methadone dose often needs increasing"),
    _I("methadone", "RTV", MONITOR, "Ritonavir-boosted darunavir lowers methadone.",
       "prezista", "4.5", (r"methadone",)),
    # ---- CNS
    _I("midazolam_oral", "RTV", CONTRAINDICATED, "Ritonavir markedly raises oral midazolam/triazolam.",
       "norvir", "4.3", (r"midazolam|triazolam",)),
    _I("midazolam_oral", "COBI", CONTRAINDICATED, "Cobicistat markedly raises oral midazolam/triazolam.",
       "rezolsta", "4.3", (r"midazolam|triazolam",)),
    _I("midazolam_oral", "EFV", CONTRAINDICATED, "Efavirenz competes for CYP3A4 with midazolam/triazolam.",
       "efavirenz", "4.3", (r"midazolam|triazolam",)),
    _I("quetiapine", "RTV", CONTRAINDICATED, "Ritonavir raises quetiapine (coma reported).",
       "norvir", "4.3", (r"quetiapine",)),
    _I("quetiapine", "COBI", CONTRAINDICATED, "Cobicistat raises quetiapine.",
       "rezolsta", "4.3", (r"quetiapine",)),
    _I("pimozide", "RTV", CONTRAINDICATED, "Ritonavir raises pimozide/lurasidone.",
       "norvir", "4.3", (r"pimozide",)),
    _I("pimozide", "COBI", CONTRAINDICATED, "Cobicistat raises pimozide/lurasidone.",
       "rezolsta", "4.3", (r"pimozide|lurasidone",)),
    _I("pimozide", "EFV", CONTRAINDICATED, "Efavirenz with pimozide — risk of arrhythmia.",
       "efavirenz", "4.3", (r"pimozide",)),
    # ---- other
    _I("sildenafil_pah", "RTV", CONTRAINDICATED, "Ritonavir raises sildenafil (PAH dosing contraindicated).",
       "norvir", "4.3", (r"sildenafil",)),
    _I("sildenafil_pah", "COBI", CONTRAINDICATED, "Cobicistat raises sildenafil (PAH dosing contraindicated).",
       "rezolsta", "4.3", (r"sildenafil",)),
    _I("colchicine", "RTV", ADJUST, "Ritonavir raises colchicine; contraindicated with renal or hepatic "
       "impairment.", "norvir", "4.3", (r"colchicine",),
       dose_change="Reduce colchicine dose; do not combine if renal or hepatic impairment"),
    _I("colchicine", "COBI", ADJUST, "Cobicistat raises colchicine; contraindicated with renal or hepatic "
       "impairment.", "rezolsta", "4.3", (r"colchicine",),
       dose_change="Reduce colchicine dose; do not combine if renal or hepatic impairment"),
    _I("ergot", "RTV", CONTRAINDICATED, "Ritonavir raises ergot alkaloids (ergotism).",
       "norvir", "4.3", (r"ergot",)),
    _I("ergot", "COBI", CONTRAINDICATED, "Cobicistat raises ergot alkaloids (ergotism).",
       "rezolsta", "4.3", (r"ergot|ergotamine",)),
    _I("ergot", "EFV", CONTRAINDICATED, "Efavirenz with ergot derivatives — risk of serious reactions.",
       "efavirenz", "4.3", (r"ergot|ergotamine",)),
    _I("sof_vel", "EFV", AVOID, "Efavirenz lowers velpatasvir.",
       "efavirenz", "4.5", (r"velpatasvir",)),
    _I("sof_vel", "TDF", MONITOR, "Sofosbuvir/velpatasvir raises tenofovir — monitor renal function.",
       "viread", "4.5", (r"velpatasvir",)),
    _I("glec_pib", "ATV", CONTRAINDICATED, "Atazanavir raises glecaprevir/pibrentasvir (ALT elevations).",
       "atazanavir", "4.3", (r"glecaprevir",)),
    _I("glec_pib", "DRV", AVOID, "Boosted darunavir raises glecaprevir/pibrentasvir.",
       "prezista", "4.5", (r"glecaprevir",)),
    _I("glec_pib", "EFV", AVOID, "Efavirenz lowers glecaprevir/pibrentasvir.",
       "efavirenz", "4.5", (r"glecaprevir",)),
)

_MORE: Tuple[Interaction, ...] = (
    # ---- hepatitis C
    _I("elbasvir", "DRV", CONTRAINDICATED, "Boosted darunavir raises grazoprevir (ALT elevations).",
       "prezista", "4.3", (r"elbasvir",)),
    _I("elbasvir", "COBI", CONTRAINDICATED, "Cobicistat-boosted darunavir raises grazoprevir.",
       "rezolsta", "4.3", (r"elbasvir",)),
    _I("elbasvir", "EFV", CONTRAINDICATED, "Efavirenz markedly lowers elbasvir and grazoprevir.",
       "efavirenz", "4.3", (r"elbasvir",)),
    _I("elbasvir", "ATV", CONTRAINDICATED, "Atazanavir raises grazoprevir.", "atazanavir", "4.3", (r"elbasvir",)),
    _I("ledipasvir", "TDF", MONITOR, "Ledipasvir/sofosbuvir raises tenofovir — monitor renal function.",
       "viread", "4.5", (r"ledipasvir",)),
    # ---- rifapentine
    _I("rifapentine", "BIC", AVOID, "Rifapentine lowers bictegravir; co-administration is not recommended.",
       "biktarvy", "4.5", (r"rifapentine", r"not recommended")),
    _I("rifapentine", "DRV", AVOID, "Rifapentine with boosted darunavir is not recommended.",
       "prezista", "4.5", (r"rifapentine and boosted PREZISTA is not recommended",)),
    _I("rifapentine", "TAF", AVOID, "Rifapentine lowers tenofovir alafenamide; not recommended.",
       "descovy", "4.5", (r"rifapentine is not recommended",)),
    _I("rifapentine", "RPV", CONTRAINDICATED, "Rifapentine markedly lowers rilpivirine.",
       "edurant", "4.3", (r"rifapentine",)),
    _I("rifapentine", "DOR", CONTRAINDICATED, "Rifapentine markedly lowers doravirine.",
       "pifeltro", "4.3", (r"rifapentine",)),
    _I("rifapentine", "CAB", CONTRAINDICATED, "Rifapentine markedly lowers cabotegravir.",
       "vocabria_tab", "4.3", (r"rifapentine",)),
    # ---- anti-infectives
    _I("clarithromycin", "RPV", AVOID, "Clarithromycin raises rilpivirine (QT prolongation); use azithromycin "
       "where possible.", "edurant", "4.5", (r"clarithromycin", r"azithromycin should be considered")),
    _I("clarithromycin", "EFV", MONITOR, "Efavirenz lowers clarithromycin; azithromycin may be considered.",
       "efavirenz", "4.5", (r"clarithromycin", r"azithromycin")),
    _I("clarithromycin", "BIC", MONITOR, "Clarithromycin may raise bictegravir — caution.",
       "biktarvy", "4.5", (r"clarithromycin", r"Caution is recommended")),
    _I("clarithromycin", "ATV", MONITOR, "Atazanavir raises clarithromycin; no dose recommendation — caution.",
       "atazanavir", "4.5", (r"clarithromycin", r"caution should be exercised")),
    _I("itraconazole", "DRV", ADJUST, "Boosted darunavir and azoles raise each other's levels.",
       "prezista", "4.5", (r"itraconazole should not exceed 200 mg",),
       dose_change="Itraconazole no more than 200 mg/day with boosted darunavir; monitor"),
    _I("itraconazole", "COBI", ADJUST, "Cobicistat-boosted darunavir and azoles raise each other's levels.",
       "rezolsta", "4.5", (r"itraconazole should not exceed 200 mg",),
       dose_change="Itraconazole no more than 200 mg/day with darunavir/cobicistat; monitor"),
    _I("voriconazole", "DRV", AVOID, "Voriconazole should not be combined with boosted darunavir unless the "
       "benefit/risk assessment justifies it.", "prezista", "4.5", (r"Voriconazole should not be combined",)),
    _I("voriconazole", "COBI", AVOID, "Voriconazole should not be combined with darunavir/cobicistat unless "
       "justified.", "rezolsta", "4.5", (r"Voriconazole should not be combined",)),
    _I("voriconazole", "EFV", ADJUST, "Efavirenz and voriconazole interact in both directions.",
       "efavirenz", "4.5", (r"voriconazole maintenance dose must be increased to 400 mg twice daily",),
       dose_change="Voriconazole 400 mg twice daily and efavirenz 300 mg once daily"),
    _I("artemether", "DRV", MONITOR, "Boosted darunavir raises lumefantrine — use with caution.",
       "prezista", "4.5", (r"artemether/lumefantrine", r"caution")),
    _I("artemether", "EFV", MONITOR, "Efavirenz lowers artemether and lumefantrine — risk of malaria treatment "
       "failure.", "efavirenz", "4.5", (r"artemether", r"caution is recommended")),
    _I("atovaquone", "EFV", AVOID, "Efavirenz lowers atovaquone and proguanil.",
       "efavirenz", "4.5", (r"atovaquone/proguanil with efavirenz should be avoided",)),
    # ---- immunosuppressants
    _I("tacrolimus", "DRV", ADJUST, "Boosted darunavir markedly raises tacrolimus/ciclosporin.",
       "prezista", "4.5", (r"Therapeutic drug monitoring of the immunosuppressive agent must be done",),
       dose_change="Therapeutic drug monitoring of tacrolimus/ciclosporin is mandatory with boosted darunavir"),
    _I("tacrolimus", "EFV", ADJUST, "Efavirenz lowers tacrolimus/ciclosporin.",
       "efavirenz", "4.5", (r"tacrolimus", r"monitoring of immunosuppressant concentrations"),
       dose_change="Monitor immunosuppressant levels for at least 2 weeks after starting or stopping efavirenz"),
    # ---- cardiovascular
    _I("dronedarone", "RTV", CONTRAINDICATED, "Ritonavir raises dronedarone/ranolazine (arrhythmia).",
       "norvir", "4.3", (r"dronedarone", r"ranolazine")),
    _I("dronedarone", "COBI", CONTRAINDICATED, "Cobicistat raises dronedarone/ranolazine.",
       "rezolsta", "4.3", (r"dronedarone", r"ranolazine")),
    _I("ivabradine", "COBI", CONTRAINDICATED, "Cobicistat raises ivabradine.", "rezolsta", "4.3", (r"ivabradine",)),
    _I("ivabradine", "DRV", CONTRAINDICATED, "Boosted darunavir raises ivabradine.",
       "prezista", "4.3", (r"ivabradine",)),
    _I("digoxin", "DRV", MONITOR, "Boosted darunavir (P-gp inhibition) raises digoxin — start low and monitor levels.",
       "prezista", "4.5", (r"digoxin",)),
    _I("lomitapide", "RTV", CONTRAINDICATED, "Ritonavir raises lomitapide (hepatotoxicity).",
       "norvir", "4.3", (r"lomitapide",)),
    _I("lomitapide", "COBI", CONTRAINDICATED, "Cobicistat raises lomitapide.", "rezolsta", "4.3", (r"lomitapide",)),
    # ---- gastrointestinal, urology
    _I("domperidone", "DRV", CONTRAINDICATED, "Boosted darunavir raises domperidone (QT prolongation).",
       "prezista", "4.3", (r"domperidone",)),
    _I("domperidone", "COBI", CONTRAINDICATED, "Cobicistat raises domperidone.", "rezolsta", "4.3", (r"domperidone",)),
    _I("naloxegol", "DRV", CONTRAINDICATED, "Boosted darunavir raises naloxegol.", "prezista", "4.3", (r"naloxegol",)),
    _I("naloxegol", "COBI", CONTRAINDICATED, "Cobicistat raises naloxegol.", "rezolsta", "4.3", (r"naloxegol",)),
    _I("alfuzosin", "RTV", CONTRAINDICATED, "Ritonavir raises alfuzosin (hypotension).", "norvir", "4.3", (r"alfuzosin",)),
    _I("alfuzosin", "COBI", CONTRAINDICATED, "Cobicistat raises alfuzosin.", "rezolsta", "4.3", (r"alfuzosin",)),
    _I("alfuzosin", "ATV", CONTRAINDICATED, "Atazanavir raises alfuzosin.", "atazanavir", "4.3", (r"alfuzosin",)),
    _I("avanafil", "RTV", CONTRAINDICATED, "Ritonavir raises avanafil.", "norvir", "4.3", (r"avanafil",)),
    _I("avanafil", "COBI", CONTRAINDICATED, "Cobicistat raises avanafil.", "rezolsta", "4.3", (r"avanafil",)),
    _I("pde5_ed", "DRV", ADJUST, "Boosted darunavir raises PDE-5 inhibitors.",
       "prezista", "4.5", (r"PDE-5 inhibitors for the treatment of erectile dysfunction",),
       dose_change="Use reduced PDE-5 inhibitor doses (e.g. sildenafil 25 mg in 48 h, tadalafil 10 mg in 72 h)"),
    # ---- CNS and analgesia
    _I("lamotrigine", "RTV", MONITOR, "Ritonavir induces glucuronidation and lowers lamotrigine.",
       "norvir", "4.5", (r"lamotrigine",)),
    _I("lamotrigine", "ATV", ADJUST, "Atazanavir/ritonavir lowers lamotrigine.",
       "atazanavir", "4.5", (r"Lamotrigine should be used with caution",),
       dose_change="Monitor lamotrigine levels and adjust the dose"),
    _I("antidepressant", "DRV", ADJUST, "Boosted darunavir alters SSRI and trazodone exposure.",
       "prezista", "4.5", (r"dose titration of the antidepressant",),
       dose_change="Titrate the antidepressant to clinical response; monitor"),
    _I("opioid", "DRV", MONITOR, "Boosted darunavir raises fentanyl and oxycodone — risk of respiratory depression.",
       "prezista", "4.5", (r"Clinical monitoring is recommended when co-administering boosted PREZISTA with these "
                           r"analgesics",)),
    # ---- endocrine, respiratory
    _I("steroid_injection", "DRV", AVOID, "Boosted darunavir raises CYP3A-metabolised corticosteroids by any route "
       "(Cushing's syndrome, adrenal suppression).", "prezista", "4.5", (r"corticosteroids \(all routes of "
                                                                         r"administration\)",)),
    _I("bosentan", "DOR", ADJUST, "Bosentan (a moderate CYP3A inducer) lowers doravirine.",
       "pifeltro", "4.5", (r"bosentan", r"doravirine dose should be increased to 100 mg twice daily"),
       dose_change="If unavoidable, doravirine 100 mg twice daily (about 12 h apart)"),
)

INTERACTIONS = INTERACTIONS + _MORE

_INDEX: Dict[Tuple[str, str], Interaction] = {(i.comed, i.drug): i for i in INTERACTIONS}


def lookup(comed: str, drug: str) -> Optional[Interaction]:
    return _INDEX.get((comed, drug))


def for_drug(drug: str) -> List[Interaction]:
    return sorted((i for i in INTERACTIONS if i.drug == drug), key=lambda i: SEVERITY_ORDER[i.severity])
