from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from crow_health.evidence.archive import archive_file
from crow_health.garmin.inventory import inventory_zip, write_inventory
from crow_health.garmin.profile import profile_json_families, write_profile
from crow_health.garmin.schema import inspect_zip_json, write_schema_profile
from crow_health.importing import ImportService, load_json_zip_member
from crow_health.parsers.defaults import default_parser_registry
from crow_health.storage import JsonlObservationStore


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="crow-health")
    sub = root.add_subparsers(dest="command", required=True)

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
    import_member.add_argument(
        "--store",
        type=Path,
        default=Path("data/observations.jsonl"),
    )

    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "archive-export":
        print(json.dumps(archive_file(args.path, args.evidence_root).to_dict(), indent=2))
    elif args.command == "inventory-export":
        inventory = inventory_zip(args.path)
        write_inventory(inventory, args.output)
        print(
            json.dumps(
                {
                    "file_count": inventory.file_count,
                    "total_bytes": inventory.total_bytes,
                    "output": str(args.output),
                },
                indent=2,
            )
        )
    elif args.command == "profile-export":
        families = profile_json_families(args.path)
        write_profile(families, args.output)
        print(
            json.dumps(
                {"json_families": len(families), "output": str(args.output)},
                indent=2,
            )
        )
    elif args.command == "inspect-json":
        schema_profile = inspect_zip_json(args.archive, args.member_path)
        write_schema_profile(schema_profile, args.output)
        print(
            json.dumps(
                {
                    "source_path": schema_profile.source_path,
                    "record_count": schema_profile.record_count,
                    "field_count": len(schema_profile.fields),
                    "output": str(args.output),
                },
                indent=2,
            )
        )
    elif args.command == "import-json-member":
        document = load_json_zip_member(args.archive, args.member_path)
        service = ImportService(
            default_parser_registry(),
            JsonlObservationStore(args.store),
        )
        report = service.import_document(document)
        print(json.dumps(asdict(report), indent=2))
        return 0 if report.persisted else 1
    return 0
