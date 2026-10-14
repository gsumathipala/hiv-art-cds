"""Clinical-safety plumbing: operating mode, knowledge-base version, audit trail.

* Mode — ``education`` (default) or ``clinical`` (``ART_CDS_MODE=clinical``). Clinical
  mode should only be enabled once the organisation's DCB0129/DCB0160 clinical-safety
  case is approved and the regulatory position (UK MDR 2002 / UKCA) is settled; see
  ``docs/clinical-safety``.
* Knowledge-base version — a fingerprint of every SmPC, guideline and knowledge file, so
  each recommendation can be traced to the exact evidence it used.
* Audit trail — one JSON line per recommendation in ``instance/audit/``: time, app and
  knowledge-base versions, mode, a SHA-256 of the inputs and the ranked output. Inputs
  themselves are not stored unless ``ART_CDS_AUDIT_INPUTS=1`` (they are clinical data).
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

PACKAGE = Path(__file__).resolve().parent
KB_SOURCES = [PACKAGE / "data", PACKAGE / "knowledge", PACKAGE / "engine"]


@lru_cache(maxsize=None)
def knowledge_base_version() -> str:
    """'KB-<newest file date>-<8-char digest>' over all data, knowledge and engine files."""
    h = hashlib.sha256()
    newest = 0.0
    for root in KB_SOURCES:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in (".json", ".txt", ".py"):
                h.update(str(path.relative_to(PACKAGE)).encode())
                h.update(path.read_bytes())
                newest = max(newest, path.stat().st_mtime)
    stamp = datetime.fromtimestamp(newest, tz=timezone.utc).strftime("%Y%m%d") if newest else "unknown"
    return f"KB-{stamp}-{h.hexdigest()[:8]}"


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _plain(v) for k, v in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


def input_digest(patient: Any) -> str:
    return hashlib.sha256(json.dumps(_plain(patient), sort_keys=True, default=str).encode()).hexdigest()


def audit(report: Any, mode: str, app_version: str, directory: Optional[Path] = None,
          store_inputs: bool = False) -> str:
    """Append one audit record and return its reference."""
    ref = uuid.uuid4().hex[:12]
    directory = directory or Path(os.environ.get("ART_CDS_AUDIT_DIR", "instance/audit"))
    directory.mkdir(parents=True, exist_ok=True)
    record: Dict[str, Any] = {
        "ref": ref,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": mode,
        "app_version": app_version,
        "kb_version": knowledge_base_version(),
        "input_sha256": input_digest(report.patient),
        "resistance_source": report.resistance.version if report.resistance else None,
        "recommended": [{"regimen": a.regimen.id, "tier": a.tier, "score": round(a.score, 1)}
                        for a in report.recommended],
        "excluded": [a.regimen.id for a in report.excluded],
        "alerts": [a.level for a in report.alerts],
    }
    if store_inputs:
        record["inputs"] = _plain(report.patient)
    path = directory / f"audit-{datetime.now(timezone.utc):%Y-%m}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    return ref
