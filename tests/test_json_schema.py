import json
import zipfile
from pathlib import Path

import pytest

from crow_health.garmin.schema import inspect_zip_json, profile_json_payload, write_schema_profile


def test_profile_json_payload_reports_types_without_values() -> None:
    payload = [
        {"calendarDate": "2026-08-01", "score": 82, "details": {"nap": False}},
        {"calendarDate": "2026-08-02", "score": None},
    ]

    profile = profile_json_payload("sleepData.json", payload)
    by_path = {field.path: field for field in profile.fields}

    assert profile.root_type == "array"
    assert profile.record_count == 2
    assert by_path["$.calendarDate"].observed_types == ("string",)
    assert by_path["$.score"].observed_types == ("integer", "null")
    assert by_path["$.details"].missing_from_records == 1
    assert "2026-08-01" not in json.dumps(profile.to_dict())


def test_inspect_zip_json_reads_exact_member_and_writes_profile(tmp_path: Path) -> None:
    archive = tmp_path / "garmin.zip"
    member = "DI_CONNECT/DI-Connect-Wellness/2026_sleepData.json"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(member, '[{"calendarDate":"2026-08-01","score":82}]')

    profile = inspect_zip_json(archive, member)
    output = tmp_path / "schema.json"
    write_schema_profile(profile, output)
    written = json.loads(output.read_text(encoding="utf-8"))

    assert written["source_path"] == member
    assert written["record_count"] == 1
    assert written["fields"][0]["path"] == "$"


def test_inspect_zip_json_rejects_unknown_member(tmp_path: Path) -> None:
    archive = tmp_path / "garmin.zip"
    with zipfile.ZipFile(archive, "w"):
        pass

    with pytest.raises(ValueError, match="JSON member not found"):
        inspect_zip_json(archive, "missing.json")
