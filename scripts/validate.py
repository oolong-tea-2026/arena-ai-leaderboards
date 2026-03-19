#!/usr/bin/env python3
"""Validate leaderboard JSON files against JSON Schemas using jsonschema."""

import json
import sys
from pathlib import Path

from jsonschema import validate, ValidationError, Draft202012Validator


def main():
    repo_root = Path(__file__).resolve().parent.parent
    schema_dir = repo_root / "schemas"

    lb_schema = json.loads((schema_dir / "leaderboard.json").read_text())
    idx_schema = json.loads((schema_dir / "index.json").read_text())

    # Compile validators
    lb_validator = Draft202012Validator(lb_schema)
    idx_validator = Draft202012Validator(idx_schema)

    # Find target dir
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    else:
        data_root = repo_root / "data"
        dirs = sorted([d for d in data_root.iterdir() if d.is_dir() and d.name[0].isdigit()])
        if not dirs:
            print("ERROR: No data directories found", file=sys.stderr)
            sys.exit(1)
        data_dir = dirs[-1]

    print(f"Validating {data_dir}", file=sys.stderr)

    all_errors: list[str] = []
    file_count = 0

    # Validate _index.json
    idx_path = data_dir / "_index.json"
    if idx_path.exists():
        data = json.loads(idx_path.read_text())
        errs = list(idx_validator.iter_errors(data))
        if errs:
            for e in errs:
                msg = f"_index.json: {e.json_path}: {e.message}"
                all_errors.append(msg)
            print(f"  ❌ _index.json: {len(errs)} errors", file=sys.stderr)
            for e in errs:
                print(f"     {e.json_path}: {e.message}", file=sys.stderr)
        else:
            print(f"  ✅ _index.json", file=sys.stderr)

        # Check for fetch errors recorded in index
        if data.get("errors"):
            for e in data["errors"]:
                msg = f"Fetch error: {e['leaderboard']}: {e['error']}"
                all_errors.append(msg)
                print(f"  ⚠️  {msg}", file=sys.stderr)
    else:
        all_errors.append("Missing _index.json")
        print(f"  ❌ Missing _index.json", file=sys.stderr)

    # Validate each leaderboard JSON
    for fp in sorted(data_dir.glob("*.json")):
        if fp.name.startswith("_"):
            continue
        file_count += 1
        data = json.loads(fp.read_text())
        errs = list(lb_validator.iter_errors(data))

        # Additional semantic checks
        if "meta" in data and "models" in data:
            declared = data["meta"].get("model_count", 0)
            actual = len(data["models"])
            if declared != actual:
                errs.append(type("Err", (), {
                    "json_path": "$.meta.model_count",
                    "message": f"declared {declared} but actual {actual}"
                })())

            ranks = [m.get("rank") for m in data["models"]]
            expected = list(range(1, len(ranks) + 1))
            if ranks != expected:
                errs.append(type("Err", (), {
                    "json_path": "$.models[*].rank",
                    "message": f"ranks not sequential 1..{len(ranks)}"
                })())

        if errs:
            for e in errs:
                path = getattr(e, "json_path", "?")
                all_errors.append(f"{fp.name}: {path}: {e.message}")
            print(f"  ❌ {fp.name}: {len(errs)} errors", file=sys.stderr)
            for e in errs:
                print(f"     {getattr(e, 'json_path', '?')}: {e.message}", file=sys.stderr)
        else:
            print(f"  ✅ {fp.name}", file=sys.stderr)

    if file_count == 0:
        all_errors.append("No leaderboard JSON files found")

    print(f"\n{file_count} files validated, {len(all_errors)} errors", file=sys.stderr)

    if all_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
