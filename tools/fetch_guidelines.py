"""Download the BHIVA guideline PDFs and extract their text for claim verification.

    python -m tools.fetch_guidelines

Writes ``art_cds/data/guidelines/<key>.txt``. ``tools/verify_smpc.py`` checks every
guideline claim the engine makes against these texts. Requires ``pypdf``.
"""
from __future__ import annotations

import sys
import urllib.request
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art_cds" / "data" / "guidelines"

DOCUMENTS = {
    "bhiva_art": "https://bhiva.org/wp-content/uploads/2025/10/"
                 "BHIVA-guidelines-on-antiretroviral-treatment-for-adults-living-with-HIV-1-2025-interim-update.pdf",
    "bhiva_pregnancy": "https://bhiva.org/wp-content/uploads/2025/06/"
                       "BHIVA-guidelines-on-the-management-of-HIV-in-pregnancy-and-the-postpartum-period.pdf",
}


def main() -> int:
    from pypdf import PdfReader

    OUT.mkdir(parents=True, exist_ok=True)
    for key, url in DOCUMENTS.items():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ART-CDS guideline reader)"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            reader = PdfReader(BytesIO(resp.read()))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        (OUT / f"{key}.txt").write_text(text, encoding="utf-8")
        print(f"ok   {key:16} {len(reader.pages)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
