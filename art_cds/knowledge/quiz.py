"""Quiz questions for teaching and revision (Dip HIV Med / specialty training level).

Every answer explanation cites the SmPC section or guideline it rests on, and those citations are
verified against the source text like the rest of the knowledge base.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..models.assessment import Ref
from .citations import bhiva, smpc_claim


@dataclass(frozen=True)
class Question:
    id: str
    topic: str
    stem: str
    options: Tuple[str, ...]
    answer: int  # index into options
    explanation: str
    refs: Tuple[Ref, ...] = ()
    case: str = ""  # optional teaching-case key to open in the decision tool


TOPICS = ("First-line ART", "Resistance", "Interactions", "Pregnancy", "Co-infection", "Long-acting",
          "Renal & bone", "Pharmacology")

QUESTIONS: Tuple[Question, ...] = (
    Question(
        "q01", "First-line ART",
        "A 28-year-old man starts ART. HBsAg positive, HLA-B*57:01 negative, HIV RNA 90,000 copies/mL, "
        "CrCl 95 mL/min. Which regimen is appropriate?",
        ("Dolutegravir/lamivudine (Dovato)", "Bictegravir/emtricitabine/tenofovir alafenamide (Biktarvy)",
         "Dolutegravir/abacavir/lamivudine (Triumeq)", "Doravirine + lamivudine (two-drug)"),
        1,
        "Chronic hepatitis B needs tenofovir plus emtricitabine or lamivudine. Dolutegravir/lamivudine is "
        "explicitly not suitable for people who need tenofovir for hepatitis B, and abacavir/lamivudine does not "
        "treat HBV adequately — lamivudine alone selects HBV resistance.",
        (bhiva("bhiva_art", "5.10", r"Who need a tenofovir-containing regimen for the treatment or prevention of "
                                    r"hepatitis B"),
         smpc_claim("dovato", "4.4", r"Lamivudine monotherapy is generally not considered an adequate treatment for "
                                     r"hepatitis B")),
        case="hbv-ckd"),
    Question(
        "q02", "Interactions",
        "A patient on rifampicin-based TB treatment needs ART. Which statement is correct?",
        ("Bictegravir can be used at the standard dose",
         "Dolutegravir can be used at 50 mg twice daily",
         "Darunavir/cobicistat is preferred", "Rilpivirine is unaffected by rifampicin"),
        1,
        "Rifampicin induces metabolism of most antiretrovirals. It is contraindicated with bictegravir, "
        "rilpivirine, doravirine, cabotegravir and boosted protease inhibitors. Dolutegravir can be given, but the "
        "dose must be doubled to 50 mg twice daily.",
        (smpc_claim("tivicay", "4.2", r"rifampicin", r"twice daily"),
         smpc_claim("biktarvy", "4.3", r"rifampicin")),
        case="tb"),
    Question(
        "q03", "Resistance",
        "A genotype shows RT K65R and M184V. Which drug is MORE active than against wild-type virus?",
        ("Tenofovir disoproxil", "Abacavir", "Zidovudine", "Emtricitabine"),
        2,
        "K65R and M184V both increase susceptibility to zidovudine — they impair the excision (primer-unblocking) "
        "mechanism that thymidine-analogue mutations rely on. Both reduce tenofovir and abacavir activity, and "
        "M184V abolishes emtricitabine activity.",
        (bhiva("bhiva_art", "7.5", r"Individuals with no or limited drug resistance"),),
        case="failure"),
    Question(
        "q04", "Pregnancy",
        "A woman conceives on darunavir/cobicistat + emtricitabine/tenofovir alafenamide. What should happen?",
        ("Continue unchanged", "Switch cobicistat to ritonavir", "Stop ART until the second trimester",
         "Switch to dolutegravir/lamivudine"),
        1,
        "Cobicistat gives inadequate darunavir exposure in pregnancy and should NOT be used as a booster; it should "
        "be switched to ritonavir as soon as possible, with darunavir 600 mg/ritonavir 100 mg twice daily if "
        "starting in pregnancy.",
        (bhiva("bhiva_pregnancy", "8.1", r"cobicistat should NOT be used as a booster in pregnancy"),),
        case="pregnancy"),
    Question(
        "q05", "Long-acting",
        "Which combination of factors raises the risk of virological failure on long-acting cabotegravir + "
        "rilpivirine?",
        ("Age over 50 and male sex", "Any two of: rilpivirine resistance mutations, subtype A6/A1, BMI ≥ 30",
         "CD4 nadir below 200 alone", "Previous abacavir hypersensitivity"),
        1,
        "The SmPC identifies three baseline factors — archived rilpivirine resistance mutations, HIV-1 subtype "
        "A6/A1, and BMI ≥ 30 kg/m². A combination of at least two is associated with failure, more often on "
        "2-monthly than monthly dosing.",
        (smpc_claim("vocabria_inj", "4.4", r"combination of at least 2 of the following baseline factors"),),
        case="long-acting"),
    Question(
        "q06", "Renal & bone",
        "A patient has osteoporosis and a previous fragility fracture. Which should be avoided?",
        ("Tenofovir alafenamide", "Tenofovir disoproxil", "Dolutegravir", "Emtricitabine"),
        1,
        "BHIVA recommends against tenofovir disoproxil in osteoporosis, severe osteopenia, previous fragility "
        "fracture, a 10-year major osteoporotic fracture probability > 5% or hip fracture probability > 1%. "
        "Tenofovir alafenamide has less effect on bone mineral density.",
        (bhiva("bhiva_art", "8.2", r"We recommend against the use of tenofovir DF in individuals with osteoporosis"),)),
    Question(
        "q07", "Pharmacology",
        "Why does dolutegravir raise serum creatinine without reducing true GFR?",
        ("It is nephrotoxic at standard doses", "It inhibits the tubular transporter OCT2",
         "It causes rhabdomyolysis", "It increases creatinine production in muscle"),
        1,
        "Dolutegravir (like bictegravir, cobicistat and rilpivirine) inhibits tubular secretion of creatinine via "
        "OCT2/MATE1. Creatinine rises early, then plateaus, with no true change in glomerular filtration. A "
        "cystatin C-based eGFR avoids this.",
        (smpc_claim("tivicay", "4.4", r"creatinine"),)),
    Question(
        "q08", "Co-infection",
        "When should ART start in a patient with cryptococcal meningitis?",
        ("Immediately, on the day of diagnosis", "After the first 2 weeks of antifungal treatment, timed "
         "individually", "Only after 6 months of antifungal treatment", "Only once the CD4 exceeds 200"),
        1,
        "Rapid ART is not recommended in cryptococcal meningitis. Most studies favour deferring beyond the first "
        "2 weeks of antifungal treatment, with the exact timing based on clinical and CSF assessment, because of "
        "the risk of raised intracranial pressure and IRIS.",
        (bhiva("bhiva_art", "5.6", r"favour deferred \(after 2 weeks\) intitiation of ART during treatment of "
                                   r"cryptococcal meningitis"),)),
    Question(
        "q09", "First-line ART",
        "Which is required before starting dolutegravir/lamivudine as first-line therapy?",
        ("CD4 above 500", "Exclusion of lamivudine and integrase resistance, HBV, and viral load < 500,000",
         "A trial of three-drug therapy first", "Genotypic tropism testing"),
        1,
        "Dovato is licensed only without known or suspected resistance to the integrase class or lamivudine. BHIVA "
        "adds a baseline viral load below 500,000 copies/mL and no need for tenofovir for hepatitis B.",
        (smpc_claim("dovato", "4.1", r"no known or suspected resistance to the integrase inhibitor class, or "
                                     r"lamivudine"),
         bhiva("bhiva_art", "5", r"Baseline viral load <500,000 copies/mL")),
        case="first-line"),
    Question(
        "q10", "Resistance",
        "A patient has a 2015 genotype showing K103N and a 2026 genotype showing no mutations. They now need a "
        "switch. Which is true?",
        ("The 2026 result supersedes the old one, so NNRTIs are safe",
         "K103N must be assumed to persist, so NNRTI-based switch is not appropriate",
         "A proviral DNA test would definitively exclude K103N",
         "K103N only matters if the viral load is above 1000"),
        1,
        "Resistance is cumulative and archived in proviral DNA. A mutation documented once must be assumed present "
        "for life; it simply becomes undetectable in plasma when the selecting drug is withdrawn. BHIVA recommends "
        "not switching to NNRTI-based ART with any NNRTI resistance. A negative proviral test does not exclude "
        "archived mutations.",
        (bhiva("bhiva_art", "5.9", r"any NNRTI resistance, we recommend not switching to NNRTI-based ART"),)),
    Question(
        "q11", "Interactions",
        "A patient taking rilpivirine needs treatment for reflux. Which is contraindicated?",
        ("Alginate antacid", "Famotidine 12 hours apart", "Omeprazole", "Lifestyle measures"),
        2,
        "Proton pump inhibitors raise gastric pH and markedly lower rilpivirine absorption; they are "
        "contraindicated. H2-antagonists can be used if separated (at least 12 hours before or 4 hours after "
        "rilpivirine), and antacids 2 hours before or 4 hours after.",
        (smpc_claim("edurant", "4.3", r"proton pump"),
         smpc_claim("edurant", "4.5", r"H2", r"12 hours", r"4 hours"))),
    Question(
        "q12", "Co-infection",
        "An infant is born to a parent on ART for 14 weeks with all viral loads < 50 copies/mL, good engagement, "
        "and a viral load of < 50 at delivery. What prophylaxis?",
        ("No prophylaxis", "Zidovudine for 2 weeks", "Zidovudine + lamivudine + nevirapine",
         "Zidovudine for 6 weeks"),
        1,
        "All the BHIVA low-risk criteria are met — ART for at least 10 weeks before delivery, good engagement, a "
        "viral load within 6 weeks, and all viral loads < 50 in the last 10 weeks — so 2 weeks of zidovudine "
        "monotherapy is recommended, started within 4 hours of birth.",
        (bhiva("bhiva_pregnancy", "11.1", r"we recommend 2 weeks of zidovudine monotherapy if all the following "
                                          r"criteria are met"),)),
)

QUESTIONS_BY_ID: Dict[str, Question] = {q.id: q for q in QUESTIONS}


def by_topic(topic: Optional[str] = None) -> List[Question]:
    return [q for q in QUESTIONS if not topic or q.topic == topic]
