#!/usr/bin/env bash
# Prepare the Codespace: install dependencies, then download the source texts.
# The SmPC download is slow (emc rate-limits to one request every 20 s), so it runs in the
# background — the teaching pages that need it fill in as it progresses.
set -euo pipefail

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "Downloading BHIVA guidelines…"
python -m tools.fetch_guidelines || echo "  (guidelines unavailable — the app still runs)"

echo "Downloading UK SmPCs in the background; this takes about 15 minutes."
nohup python -m tools.fetch_smpc --delay 20 > /tmp/fetch_smpc.log 2>&1 &

cat <<'MSG'

  ART Navigator UK is ready.

    python run.py            start the app (port 5000 is forwarded automatically)
    python -m pytest -q      run the tests
    tail -f /tmp/fetch_smpc.log   watch the SmPC download

  Created by Saranga Sumathipala. Education mode — not a medical device.

MSG
