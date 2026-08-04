from __future__ import annotations

import argparse
import json
from pathlib import Path

from crow_health.evidence.archive import archive_file
from crow_health.garmin.inventory import inventory_zip, write_inventory
from crow_health.garmin.profile import profile_json_families, write_profile


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
    return root


def main() -> int:
    args = parser().parse_args()
    if args.command == "archive-export":
        print(json.dumps(archive_file(args.path, args.evidence_root).to_dict(), indent=2))
    elif args.command == "inventory-export":
        inventory = inventory_zip(args.path)
        write_inventory(inventory, args.output)
        print(json.dumps({"file_count": inventory.file_count, "total_bytes": inventory.total_bytes, "output": str(args.output)}, indent=2))
    elif args.command == "profile-export":
        families = profile_json_families(args.path)
        write_profile(families, args.output)
        print(json.dumps({"json_families": len(families), "output": str(args.output)}, indent=2))
    return 0
