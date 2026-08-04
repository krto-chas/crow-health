from pathlib import Path

from crow_health.evidence.archive import archive_file, sha256_file


def test_archive_is_content_addressed_and_idempotent(tmp_path: Path) -> None:
    source = tmp_path / "garmin.zip"
    source.write_bytes(b"garmin")
    first = archive_file(source, tmp_path / "evidence")
    second = archive_file(source, tmp_path / "evidence")
    assert first.evidence_id == second.evidence_id
    assert first.sha256 == sha256_file(source)
    assert Path(first.archived_path).read_bytes() == b"garmin"
