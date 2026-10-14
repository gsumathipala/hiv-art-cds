# Clinical safety and regulatory position

ART Navigator UK runs in **education mode** by default. Do not switch to clinical mode
(`ART_CDS_MODE=clinical`) until everything below is in place.

## Intended use

- **Users**: HIV physicians, HIV pharmacists and trainees in UK HIV services.
- **Purpose (clinical mode)**: to support, not replace, the choice of antiretroviral
  regimen for adults with HIV by showing, for a given patient, which regimens are
  appropriate under BHIVA guidance and UK SmPCs, and why.
- **Purpose (education mode)**: teaching antiretroviral pharmacology, resistance and
  guideline application; not for decisions about individual patients.
- **Out of scope**: children and adolescents under 18, PrEP/PEP prescribing, salvage
  regimen construction (flagged for MDT), automatic prescribing.

## Regulatory position (to be confirmed by the deploying organisation)

Software that analyses an individual patient's data to recommend treatment is likely to
be a **medical device** under the UK Medical Devices Regulations 2002 (software as a
medical device; MHRA guidance on software and AI as a medical device). Clinical use would
then need UKCA marking (or a valid route under current MHRA transitional arrangements),
registration with the MHRA, and post-market surveillance. Take regulatory advice before
any clinical deployment. In education mode the tool is presented as teaching material,
not for individual patient management.

## NHS clinical risk management

- **DCB0129** (manufacturer): a named Clinical Safety Officer (CSO), a clinical risk
  management plan, the hazard log, and a clinical safety case report for each release.
- **DCB0160** (deploying organisation): the organisation's own CSO, local hazard
  assessment and safety case before go-live.
- Also relevant: DTAC (Digital Technology Assessment Criteria), the Data Security and
  Protection Toolkit, and a DPIA if any patient data is processed or stored.

## What the software provides

| Control | Where |
| --- | --- |
| Hazard log (initial developer assessment, DCB0129 risk matrix) | `art_cds/safety.py`, shown at `/learn/governance` |
| Versioned knowledge base — fingerprint of every SmPC, guideline and rule file | footer and report "Traceability" panel |
| Audit trail — one line per recommendation, input hash only by default | `instance/audit/audit-YYYY-MM.jsonl` |
| Source verification — every SmPC/BHIVA claim checked against the text | `python -m tools.verify_smpc`, run by the test suite |
| Change detection for SmPCs | `python -m tools.check_updates` |

## Safety case template (DCB0129)

1. Introduction and scope of this release (app version, knowledge-base version).
2. System description and intended use (above).
3. Clinical risk management process and CSO sign-off.
4. Hazard log summary with residual risk ratings.
5. Test evidence: automated tests, claim verification report, clinical validation
   against MDT decisions (to be done).
6. Outstanding issues and conditions for deployment.
7. Approval: CSO name, registration, date.
