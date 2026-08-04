from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

from crow_health.parsers.models import SourceDocument


def load_json_zip_member(archive: Path, member_path: str) -> SourceDocument:
    with ZipFile(archive) as handle:
        try:
            raw = handle.read(member_path)
        except KeyError as exc:
            raise FileNotFoundError(f"ZIP member not found: {member_path}") from exc

    checksum = sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"ZIP member is not valid UTF-8 JSON: {member_path}") from exc

    if not isinstance(payload, (dict, list)):
        raise TypeError("JSON source root must be an object or array")

    return SourceDocument(
        evidence_id=checksum,
        source_path=member_path,
        media_type="application/json",
        checksum=checksum,
        payload=payload,
    )
