# ART Navigator UK

**Created by Saranga Sumathipala.**

A Flask web application that is both a **clinical decision support system** for choosing
antiretroviral therapy for adults with HIV in the UK, and a **teaching tool** for HIV
physicians. Every clinical statement it makes is checked, automatically, against the UK
Summary of Product Characteristics (SmPC) or BHIVA guideline text it cites.

> **Education mode by default — not a medical device.** Software that recommends treatment
> for an individual patient is likely to be a medical device under the UK Medical Devices
> Regulations 2002. This build has no UKCA marking and no approved clinical safety case.
> See [docs/clinical-safety](docs/clinical-safety/README.md).

## What it does

### Decision support

Enter the patient's virology, immunology, organ function, co-infections, resistance history,
co-medications and preferences. You get regimens ranked against current BHIVA guidance, each
showing:

- the actual tablets the patient would take, drawn to scale from the SmPC description;
- UK dosing, food requirements and any dose adjustment (for example dolutegravir twice daily
  with rifampicin);
- every reason for the ranking, each citing an SmPC section or guideline paragraph;
- a monitoring plan, and the excluded regimens with their reasons.

Outputs: a **clinic letter / GP summary**, a plain-English **patient leaflet** with pictures of
their own tablets, and a **JSON API**. Cases can be saved to and reloaded from a local file, and
a **FHIR R4 bundle** can be imported to pre-fill the form.

### Teaching

An HIV life-cycle diagram linked to drug classes; a monograph for each drug (mechanism,
pharmacokinetics quoted from SmPC §5.2, an adverse-effect chart by frequency, dosing,
interactions, pregnancy, resistance); the full SmPC for 37 UK products; a formulary of
tablet drawings; an interaction matrix; a resistance primer and an **interactive resistance
explorer**; **concentration–time curves**; six worked cases; and a **quiz** with cited feedback.

### Tools

| Tool | What it does |
| --- | --- |
| Calculators | Cockcroft–Gault CrCl, CKD-EPI 2021 creatinine / 2012 cystatin C / 2021 combined eGFR, Child-Pugh, QRISK3-2017, FRAX link |
| Long-acting planner | CAB + RPV and lenacapavir schedules with the dosing windows, missed-injection rules, oral bridging, failure-risk check, calendar (.ics) download |
| Perinatal planner | Infant post-natal prophylaxis risk category and regimen, intrapartum intravenous zidovudine, infant testing |
| Source watch | Re-fetches every SmPC, diffs it and re-verifies every claim; runs weekly in CI |

## Evidence and verification

| What | Source |
| --- | --- |
| Product facts — appearance, dosing, renal/hepatic limits, contraindications, interactions, pregnancy, adverse reactions, pharmacokinetics | UK **SmPCs** from the [electronic medicines compendium](https://www.medicines.org.uk/emc) |
| Regimen tiers and guideline rules | **BHIVA** adult ART guidelines 2022 (2025 interim update) |
| Starting ART in pregnancy, infant prophylaxis | **BHIVA** pregnancy and postpartum guidelines (2025) |
| Tuberculosis | **BHIVA** TB guidelines 2018 (2023 interim update) |
| Resistance | **Stanford HIVdb** (opt-in, live) or a local teaching approximation |
| Cardiovascular risk | **QRISK3-2017** (ClinRisk, LGPL), validated against all 97 reference scores |
| Long-acting cabotegravir + rilpivirine | NICE TA757 |

**Every SmPC and BHIVA statement is verified against the source text.** Each citation records
the wording that must appear in the section it cites; `python -m tools.verify_smpc` fails if
any does not. There are **345 such claims** and the test suite runs the check. Building this
verification exposed several places where UK practice differs from US labelling, and the
knowledge base follows the UK sources — for example Rezolsta must not be started below
CrCl 70 mL/min with FTC/3TC/TDF; the generic efavirenz/emtricitabine/tenofovir disoproxil
tablet is licensed only for switching; dofetilide is not a UK product, so the dolutegravir
contraindication is fampridine.

**Tablet pictures are drawings, not photographs.** Manufacturers' photographs are copyrighted,
so each dose unit is drawn to scale from the colour, shape, size and debossing in SmPC §3, with
that wording shown beside it. Licensed photographs can replace a drawing by saving them as
`art_cds/static/img/products/<product key>.jpg`.

## Running it

```bash
git clone https://github.com/gsumathipala/hiv-art-cds.git
cd hiv-art-cds
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Download the sources (they are not redistributed with this repository)
.venv/bin/python -m tools.fetch_guidelines     # BHIVA PDFs, ~1 minute
.venv/bin/python -m tools.fetch_smpc           # 37 UK SmPCs, ~15 minutes (emc rate limits)
.venv/bin/python -m tools.verify_smpc          # should report 345/345 claims verified

.venv/bin/python run.py                        # http://127.0.0.1:5000
.venv/bin/python -m pytest -q                  # 305 tests
```

On macOS, use `127.0.0.1:5000` rather than `localhost:5000` — AirPlay Receiver occupies
port 5000 under the name `localhost`.

### In the browser, with no install

Open the repository in **GitHub Codespaces** (Code → Codespaces → Create codespace). The
dev container installs everything, downloads the guidelines and starts the app automatically;
the SmPC download then runs in the background.

### Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `ART_CDS_MODE` | `education` | `clinical` removes the education banner. Only with an approved safety case. |
| `ART_CDS_SECRET_KEY` | dev value | Flask secret key. |
| `ART_CDS_AUDIT` | `1` | Write an audit line per recommendation. |
| `ART_CDS_AUDIT_INPUTS` | `0` | Also store the inputs (clinical data — off by default). |

## How a recommendation is made

1. Regimens available in the scenario (first-line, first-line in pregnancy, suppressed switch,
   virological failure) start from their BHIVA tier — 100, 80 or 60 points.
2. Twelve independent rule modules assess each regimen: HLA-B\*57:01, hepatitis B, HIV-2,
   co-infection, renal and hepatic limits, licensed indication, pregnancy, treatment history,
   resistance, interactions, tolerability and the patient's priorities.
3. Each finding **excludes** the regimen, scores it **down** (caution), scores it **up**
   (benefit), or adds **information** — and cites its source.
4. Regimens are ranked by the resulting score; excluded ones are listed with their reasons.

## Architecture

```
art_cds/
  models/            PatientProfile, GenotypeTest, LabValue, ArtEpisode; Finding, Report, Ref
  knowledge/         the data — nothing here makes decisions
    products.py        UK products ↔ emc SmPC ids          smpc.py       SmPC loader and views
    drugs.py           substances, classes, mechanisms     regimens.py   UK regimens and dosing
    guidelines.py      BHIVA tiers per scenario, cited     citations.py  verifiable citations
    organ_limits.py    renal/hepatic limits per product    interactions.py  53 co-medications
    resistance.py      mutation penalty scores             medicines.py  name → co-medication
    conditions.py      comorbidities                       cases.py      teaching cases
    quiz.py            quiz questions with cited answers
  engine/
    rules/             one module per clinical concern, each returning cited findings
    resistance.py      cumulative genotype, HIVdb or local scoring, GSS
    recommender.py     candidates → rules → ranked report   virology.py  blip/LLV/failure
    alerts.py          patient-level alerts                 monitoring.py  monitoring plan
  calculators/       CrCl, eGFR, Child-Pugh, QRISK3 (LGPL translation)
  visuals/           pills.py (SmPC §3 → SVG), timeline.py, pharmacokinetics.py
  web/               blueprints: assess, learn, calculators, longacting, perinatal, quiz, explore, api
  hivdb.py  longacting.py  perinatal.py  fhir.py  governance.py  safety.py  verification.py
tools/
  fetch_smpc.py  fetch_guidelines.py  verify_smpc.py  check_updates.py
```

Adding a consideration means one rule module and one line in `engine/rules/__init__.py`.
Adding a product means one line in `products.py` and a fetch. Adding a regimen means an entry
in `regimens.py` and its tiers in `guidelines.py`.

## Clinical safety and governance

- Education mode by default, with the banner and a watermark on every report.
- A versioned knowledge base fingerprint on every report, letter and API response.
- An append-only audit trail (input hash only, unless inputs are explicitly enabled).
- A DCB0129-style hazard log, shown at `/learn/governance` with live verification status.
- `docs/clinical-safety/` covers intended use, the MHRA/UKCA position, DCB0129/DCB0160
  responsibilities and a safety-case template.

## Scope and limitations

Adults only. The interaction table covers 53 co-medications and is not exhaustive — a blank
cell means "not in this table", not "no interaction"; always check the
[Liverpool HIV interaction checker](https://www.hiv-druginteractions.org). The local
resistance scores are an abridged teaching model; enable Stanford HIVdb for the real
algorithm. Salvage therapy beyond flagging the need for MDT input is out of scope. First-line,
switch and pregnancy tiers follow the BHIVA tables directly; the virological-failure tiers
apply the principles of section 7, which is written as principles rather than a table.

## Licence

MIT, © 2026 Saranga Sumathipala — except `art_cds/calculators/qrisk3_raw.py`, which is a
translation of ClinRisk's QRISK3-2017 and is LGPL v3 or later. SmPC and BHIVA text is the
copyright of its owners and is **not** distributed here; the fetch tools download it for you.
See [LICENSE](LICENSE).
