# UK Summaries of Product Characteristics

Parsed copies of the UK SmPC for each product in `art_cds/knowledge/products.py` live here.
**They are not stored in this repository**: SmPC text is the copyright of the respective
marketing authorisation holders and is published on the
[electronic medicines compendium](https://www.medicines.org.uk/emc).

```bash
python -m tools.fetch_smpc            # all products, ~15 minutes (emc rate-limits requests)
python -m tools.fetch_smpc biktarvy   # or just one
python -m tools.verify_smpc           # check every claim against the downloaded text
python -m tools.check_updates         # re-fetch and diff against what you already have
```

The application reads only these parsed copies; it never contacts emc at run time. Without them
the decision engine still works — the rules live in code — but product pages, adverse-effect
charts and SmPC citations are unavailable.
