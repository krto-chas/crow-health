import json
import zipfile
from pathlib import Path

from crow_health.garmin.inventory import inventory_zip, write_inventory


def test_inventory_zip(tmp_path: Path) -> None:
    archive = tmp_path / "export.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("a/data.json", '{"x": 1}')
        zf.writestr("b/raw.fit", b"fit")
    inventory = inventory_zip(archive)
    assert inventory.file_count == 2
    assert inventory.suffix_counts == {".fit": 1, ".json": 1}
    output = tmp_path / "inventory.json"
    write_inventory(inventory, output)
    assert json.loads(output.read_text())["file_count"] == 2
