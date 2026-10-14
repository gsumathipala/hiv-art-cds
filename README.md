# ART Navigator UK

A Flask web app that is both a **clinical decision support system** for choosing
antiretroviral therapy for adults with HIV-1 in the UK and a **teaching tool** for
HIV physicians.

- **Assess a patient** — enter virology, CD4, renal and hepatic function, HBV,
  HLA-B\*57:01, resistance mutations, pregnancy, comorbidities, co-medications and
  the patient's priorities. You get ranked regimens with the tablets the patient
  will take, dosing, dose adjustments, a monitoring plan, and every reason for the
  ranking — each one cited to a UK SmPC section or a BHIVA guideline. Excluded
  regimens are listed with their reasons.
- **Learn** — HIV life-cycle diagram with drug-class targets, class pages, drug
  monographs (mechanism, pharmacokinetics quoted from SmPC §5.2, adverse-reaction
  frequency grid from §4.8, dosing, interactions, pregnancy, resistance), a UK
  formulary drawn from the SmPC descriptions, an interaction matrix, a resistance
  primer and six worked teaching cases.

> **For use by HIV clinicians.** It supports, and does not replace, clinical
> judgement, the current SmPC, BHIVA guidance, the Liverpool HIV interaction
> checker and your HIV MDT.

## Sources

| What | Source |
| --- | --- |
| Every product fact — appearance, dosing, renal/hepatic limits, contraindications, interactions, pregnancy, adverse reactions, pharmacology | UK **Summary of Product Characteristics** from the electronic medicines compendium (emc, medicines.org.uk) |
| Regimen tiers and guideline rules | BHIVA adult ART guidelines 2022, **2025 interim update** (Tables 5.1, 5.2; sections 5, 7, 8) |
| Starting ART in pregnancy; pregnancy dosing and monitoring | BHIVA pregnancy and postpartum guidelines **2025** (Tables 8.1–8.3) |
| TB, hepatitis, routine monitoring | Other BHIVA guidelines (cited by name, not text-checked); NICE TA757 for long-acting cabotegravir + rilpivirine |
| Resistance scoring | Simplified penalty scores modelled on Stanford HIVdb (teaching approximation) |

**Every SmPC and BHIVA statement is checked against the source text.** Each citation records
patterns that must occur in the cited SmPC section or guideline; `tools/verify_smpc.py`
(and the test suite) fails if any does not — 287 claims at present. Regimen tiers each link
to the BHIVA table entry they come from. Building this check exposed
several places where UK SmPCs differ from US labels, and the knowledge base follows
the UK texts. For example, Rezolsta must not be started below CrCl 70 mL/min with
FTC/3TC/TDF, generic efavirenz/emtricitabine/tenofovir disoproxil is licensed only for
switching, and the UK raltegravir SmPC says doubling the dose with rifampicin "can be
considered".

**Tablet pictures are drawings, not photographs.** Manufacturer photographs are
copyrighted, so each tablet, capsule and injection is drawn to scale from the colour,
shape, size and debossing in SmPC §3; the verbatim §3 text appears beside it. To use
licensed photographs instead, put them at `art_cds/static/img/products/<product key>.jpg`
(or `.png`/`.webp`) — they replace the drawing automatically.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py            # http://127.0.0.1:5000
.venv/bin/python -m pytest         # 122 tests
```

The parsed SmPCs are in `art_cds/data/smpc/`. To refresh them from emc:

```bash
.venv/bin/python -m tools.fetch_smpc --refresh   # ~20 s between requests; stops if emc asks for a human check
.venv/bin/python -m tools.fetch_guidelines       # BHIVA PDFs -> art_cds/data/guidelines (needs pypdf)
.venv/bin/python -m tools.verify_smpc            # re-check every claim against the new text
```

SmPC text is © the marketing authorisation holders and is reproduced from emc;
check emc's terms before redistributing the app with the SmPC data. The extracted BHIVA
guideline text in `art_cds/data/guidelines` is © BHIVA and is kept only for claim
verification.

## Architecture

```
art_cds/
  models/            PatientProfile; Finding, RegimenAssessment, Report, Ref (citations)
  knowledge/         the data — nothing here makes decisions
    products.py        UK products ↔ emc SmPC ids
    smpc.py            SmPC loader; adverse-reaction grid; §5.2 pharmacokinetic sentences
    drugs.py           substances, classes, mechanisms
    regimens.py        regimens as prescribed in the UK (which products, dosing)
    guidelines.py      BHIVA tiers per scenario (first-line, pregnancy, switch, failure), each cited
    citations.py       verifiable SmPC and BHIVA citations
    organ_limits.py    per-product renal/hepatic limits from SmPC §4.2/4.3
    interactions.py    co-medication interactions from SmPC §4.3/4.5
    resistance.py      mutation penalty scores
    cases.py           teaching cases
  engine/
    rules/             one module per clinical concern, each returning cited findings:
                       hla, hepatitis_b, organ, indication (SmPC §4.1 licensing), pregnancy,
                       history, resistance, interactions, tolerability, preferences
    resistance.py      genotype parsing and scoring, GSS
    recommender.py     candidates → rules → ranked report
    alerts.py          patient-level alerts (prophylaxis, missing tests, TB/crypto timing)
    monitoring.py      monitoring plan per regimen
  visuals/pills.py   SmPC §3 text → to-scale SVG drawings
  web/               blueprints: assess (form + report), learn (teaching pages), api (JSON)
tools/
  fetch_smpc.py      polite emc downloader/parser
  fetch_guidelines.py  BHIVA PDF downloader/text extractor
  verify_smpc.py     checks every SmPC and BHIVA claim against the text
```

Adding a consideration means adding one rule module (decorated with `@rule`) and
importing it in `engine/rules/__init__.py`. Adding a product means one line in
`products.py` and a fetch. Adding a regimen means one entry in `regimens.py` and its
tiers in `guidelines.py`.

### Scoring

Each regimen starts at its BHIVA tier (preferred 100, alternative 80, other 60). Each
finding is one of four kinds:

- **exclude**: contraindicated, or outside the licence;
- **caution**: scored down;
- **benefit**: scored up;
- **info**: no score change.

Regimens are ranked by the resulting score.

### API

`POST /api/assess` takes the same fields as the form, as JSON, and returns the report.
`GET /api/products` lists products with their SmPC versions.

## Scope and limitations

The tool covers adults only. The interaction table covers 53 co-medications (149 SmPC-verified
interactions) and is not exhaustive; a blank cell is not "no interaction". The
resistance scores are an abridged teaching model. Salvage therapy beyond flagging the
need for MDT input is out of scope. First-line, switch and pregnancy tiers follow the BHIVA tables
directly; section 7 of the adult guideline gives principles rather than a table for
virological failure, so failure tiers apply those principles.
