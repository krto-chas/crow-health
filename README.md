# Crow Health RC0 — Evidence Foundation

RC0 receives a Garmin export, archives it unchanged, inventories files and profiles JSON structures. It does not normalize health records, analyze health, publish to Home Assistant or make medical claims.

## Windows / Git Bash

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -e '.[dev]'
pytest -q
crow-health archive-export "/c/path/to/garmin.zip"
crow-health inventory-export "/c/path/to/garmin.zip"
crow-health profile-export "/c/path/to/garmin.zip"
```

## Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

Generated inventory/profile files may contain filenames or identifiers. Treat them as personal data and do not commit them.
