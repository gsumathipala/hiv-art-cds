"""Comorbidities and circumstances the rules respond to."""
from __future__ import annotations

COMORBIDITIES = {
    "cvd": "Established cardiovascular disease or high QRISK3",
    "osteoporosis": "Osteopenia, osteoporosis or fragility fracture",
    "psychiatric": "Depression, suicidality or other significant mental illness",
    "weight": "Obesity or concern about weight gain",
    "dyslipidaemia": "Dyslipidaemia",
    "diabetes": "Diabetes mellitus",
    "active_tb": "Active tuberculosis",
    "cns_tb": "CNS tuberculosis (including TB meningitis)",
    "crypto_meningitis": "Cryptococcal meningitis (current)",
}
