"""Check every SmPC and BHIVA claim the engine makes against the source text.

    python -m tools.verify_smpc

A claim is (product, section, patterns): every pattern must occur in that
section of that product's SmPC. Claims for products whose SmPC has not been
downloaded are reported as missing. Exits non-zero if any claim fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from art_cds.verification import check  # noqa: E402


def main() -> int:
    failures, missing, total = check()
    for line in missing:
        print("MISSING ", line)
    for line in failures:
        print("FAIL    ", line)
    print(f"{total - len(failures) - len(missing)}/{total} claims verified against the SmPC/BHIVA text; "
          f"{len(failures)} failed, {len(missing)} missing.")
    return 1 if failures or missing else 0


if __name__ == "__main__":
    sys.exit(main())
