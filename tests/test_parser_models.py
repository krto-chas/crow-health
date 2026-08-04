from __future__ import annotations

from crow_health.parsers.models import ParseMessage, ParseResult, SourceDocument


def test_source_document_preserves_provenance_fields() -> None:
    document = SourceDocument(
        evidence_id="evidence-42",
        source_path="wellness/sleepData.json",
        media_type="application/json",
        checksum="deadbeef",
        payload={"items": []},
    )

    assert document.evidence_id == "evidence-42"
    assert document.checksum == "deadbeef"
    assert document.payload == {"items": []}


def test_parse_result_success_keeps_warnings_and_clears_errors() -> None:
    warning = ParseMessage(code="missing_optional", message="Optional field absent")

    result = ParseResult.success(
        records=(),
        warnings=(warning,),
        parser_name="sleep",
        parser_version="1.0.0",
        source_evidence_id="evidence-42",
    )

    assert result.warnings == (warning,)
    assert result.errors == ()
    assert result.source_evidence_id == "evidence-42"
