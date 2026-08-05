from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from crow_health.evidence.archive import archive_file
from crow_health.garmin.full_import import run_garmin_sleep_import
from crow_health.garmin.inventory import inventory_zip, write_inventory
from crow_health.garmin.profile import profile_json_families, write_profile
from crow_health.garmin.schema import inspect_zip_json, write_schema_profile
from crow_health.importing import BatchImportService, ImportService, load_json_zip_member
from crow_health.parsers.defaults import default_parser_registry
from crow_health.runtime import runtime_identity
from crow_health.storage import JsonlObservationIndex, JsonlObservationStore, ObservationQuery
from crow_health.validation import validate_store


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="crow-health")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("version")

    archive = sub.add_parser("archive-export")
    archive.add_argument("path", type=Path)
    archive.add_argument("--evidence-root", type=Path, default=Path("data/evidence"))

    inventory = sub.add_parser("inventory-export")
    inventory.add_argument("path", type=Path)
    inventory.add_argument("--output", type=Path, default=Path("data/garmin_inventory.json"))

    profile = sub.add_parser("profile-export")
    profile.add_argument("path", type=Path)
    profile.add_argument("--output", type=Path, default=Path("data/garmin_json_profile.json"))

    inspect_json = sub.add_parser("inspect-json")
    inspect_json.add_argument("archive", type=Path)
    inspect_json.add_argument("member_path")
    inspect_json.add_argument("--output", type=Path, default=Path("data/json_schema_profile.json"))

    import_member = sub.add_parser("import-json-member")
    import_member.add_argument("archive", type=Path)
    import_member.add_argument("member_path")
    import_member.add_argument("--store", type=Path, default=Path("data/observations.jsonl"))

    import_batch = sub.add_parser("import-json-batch")
    import_batch.add_argument("archive", type=Path)
    import_batch.add_argument("--pattern", action="append", default=None)
    import_batch.add_argument("--store", type=Path, default=Path("data/observations.jsonl"))

    index_build = sub.add_parser("index-build")
    index_build.add_argument("--store", type=Path, default=Path("data/observations.jsonl"))
    index_build.add_argument("--index", type=Path, default=None)

    index_query = sub.add_parser("index-query")
    index_query.add_argument("--store", type=Path, default=Path("data/observations.jsonl"))
    index_query.add_argument("--index", type=Path, default=None)
    index_query.add_argument("--metric")
    index_query.add_argument("--source-evidence-id")
    index_query.add_argument("--parser-name")
    index_query.add_argument("--from", dest="observed_from", type=datetime.fromisoformat)
    index_query.add_argument("--to", dest="observed_to", type=datetime.fromisoformat)

    validate = sub.add_parser("validate-store")
    validate.add_argument("--store", type=Path, default=Path("data/observations.jsonl"))
    validate.add_argument("--index", type=Path, default=None)
    validate.add_argument("--no-rebuild-index", action="store_true")

    garmin_sleep = sub.add_parser("garmin-sleep-import")
    garmin_sleep.add_argument("archive", type=Path)
    garmin_sleep.add_argument("--store", type=Path, default=Path("data/observations.jsonl"))
    garmin_sleep.add_argument("--index", type=Path, default=None)
    garmin_sleep.add_argument("--pattern", action="append", default=None)
    garmin_sleep.add_argument("--output", type=Path, default=None)
    return root


def _import_service(store: Path) -> ImportService:
    return ImportService(default_parser_registry(), JsonlObservationStore(store))


def main() -> int:
    args = parser().parse_args()
    if args.command == "version":
        print(json.dumps(runtime_identity().to_dict(), indent=2))
    elif args.command == "archive-export":
        print(json.dumps(archive_file(args.path, args.evidence_root).to_dict(), indent=2))
    elif args.command == "inventory-export":
        inventory = inventory_zip(args.path)
        write_inventory(inventory, args.output)
        print(json.dumps({"file_count": inventory.file_count, "total_bytes": inventory.total_bytes, "output": str(args.output)}, indent=2))
    elif args.command == "profile-export":
        families = profile_json_families(args.path)
        write_profile(families, args.output)
        print(json.dumps({"json_families": len(families), "output": str(args.output)}, indent=2))
    elif args.command == "inspect-json":
        schema_profile = inspect_zip_json(args.archive, args.member_path)
        write_schema_profile(schema_profile, args.output)
        print(json.dumps({"source_path": schema_profile.source_path, "record_count": schema_profile.record_count, "field_count": len(schema_profile.fields), "output": str(args.output)}, indent=2))
    elif args.command == "import-json-member":
        report = _import_service(args.store).import_document(load_json_zip_member(args.archive, args.member_path))
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.persisted else 1
    elif args.command == "import-json-batch":
        report = BatchImportService(_import_service(args.store)).import_zip(args.archive, patterns=tuple(args.pattern or ("*sleepData.json",)))
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.succeeded else 1
    elif args.command == "index-build":
        index = JsonlObservationIndex(args.store, args.index)
        print(json.dumps({"entries": index.rebuild(), "index": str(index.index_path)}, indent=2))
    elif args.command == "index-query":
        index = JsonlObservationIndex(args.store, args.index)
        observations = index.query(ObservationQuery(metric=args.metric, source_evidence_id=args.source_evidence_id, parser_name=args.parser_name, observed_from=args.observed_from, observed_to=args.observed_to))
        print(json.dumps([asdict(item) for item in observations], indent=2, default=str))
    elif args.command == "validate-store":
        report = validate_store(args.store, args.index, rebuild_index=not args.no_rebuild_index)
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.succeeded else 1
    elif args.command == "garmin-sleep-import":
        report = run_garmin_sleep_import(args.archive, args.store, args.index, patterns=tuple(args.pattern or ("*sleepData.json",)))
        payload = report.to_dict()
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return 0 if report.succeeded else 1
    return 0
