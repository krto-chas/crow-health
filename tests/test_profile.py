import zipfile
from pathlib import Path

from crow_health.garmin.profile import profile_json_families


def test_profile_groups_dated_json_files(tmp_path: Path) -> None:
    archive = tmp_path / "export.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(
            "DI/a/2026-01-01_2026-02-01_1_sleepData.json",
            '[{"calendarDate":"2026-01-01","score":1}]',
        )
        zf.writestr(
            "DI/a/2026-02-01_2026-03-01_1_sleepData.json",
            '[{"calendarDate":"2026-02-01","score":2}]',
        )
    families = profile_json_families(archive)
    assert len(families) == 1
    assert families[0].file_count == 2
    assert families[0].observed_keys == ("calendarDate", "score")
