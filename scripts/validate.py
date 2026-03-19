#!/usr/bin/env python3
"""Validate leaderboard JSON files against schemas."""

import json
import sys
from pathlib import Path


def validate_json_schema(data: dict, schema: dict, path: str) -> list[str]:
    """Minimal JSON Schema validator (no external deps). Returns list of errors."""
    errors = []
    
    def check(value, sch, loc):
        t = sch.get("type")
        
        # Handle type as list (e.g., ["string", "null"])
        if isinstance(t, list):
            if value is None and "null" in t:
                return
            actual_types = [tt for tt in t if tt != "null"]
            t = actual_types[0] if actual_types else None
            if value is None:
                errors.append(f"{loc}: expected {sch['type']}, got null")
                return
        elif t and value is None and t != "null":
            if "null" not in str(sch.get("type", "")):
                errors.append(f"{loc}: unexpected null")
                return
        
        # enum check
        if "enum" in sch:
            if value not in sch["enum"]:
                errors.append(f"{loc}: {value!r} not in {sch['enum']}")
            return
        
        if t == "object" and isinstance(value, dict):
            for req in sch.get("required", []):
                if req not in value:
                    errors.append(f"{loc}: missing required field '{req}'")
            
            props = sch.get("properties", {})
            addl = sch.get("additionalProperties")
            for k, v in value.items():
                if k in props:
                    check(v, props[k], f"{loc}.{k}")
                elif addl is not None and addl is not True:
                    if isinstance(addl, dict):
                        check(v, addl, f"{loc}.{k}")
                    elif addl is False:
                        errors.append(f"{loc}: unexpected field '{k}'")
            
            mp = sch.get("minProperties")
            if mp and len(value) < mp:
                errors.append(f"{loc}: needs >= {mp} properties, got {len(value)}")
                
        elif t == "array" and isinstance(value, list):
            mi = sch.get("minItems")
            if mi and len(value) < mi:
                errors.append(f"{loc}: needs >= {mi} items, got {len(value)}")
            items_sch = sch.get("items")
            if items_sch:
                # Resolve $ref
                if "$ref" in items_sch:
                    ref_path = items_sch["$ref"].split("/")
                    ref_sch = schema
                    for part in ref_path:
                        if part == "#":
                            continue
                        ref_sch = ref_sch[part]
                    items_sch = ref_sch
                for i, item in enumerate(value):
                    check(item, items_sch, f"{loc}[{i}]")
                    
        elif t == "string":
            if not isinstance(value, str):
                errors.append(f"{loc}: expected string, got {type(value).__name__}")
            else:
                ml = sch.get("minLength")
                if ml and len(value) < ml:
                    errors.append(f"{loc}: string too short (min {ml})")
                pat = sch.get("pattern")
                if pat:
                    import re
                    if not re.match(pat, value):
                        errors.append(f"{loc}: doesn't match pattern {pat}")
                        
        elif t == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"{loc}: expected integer, got {type(value).__name__}")
            else:
                mi = sch.get("minimum")
                if mi is not None and value < mi:
                    errors.append(f"{loc}: {value} < minimum {mi}")

    check(data, schema, path)
    return errors


def main():
    repo_root = Path(__file__).resolve().parent.parent
    schema_dir = repo_root / "schemas"
    
    lb_schema = json.loads((schema_dir / "leaderboard.json").read_text())
    idx_schema = json.loads((schema_dir / "index.json").read_text())
    
    # Find the target dir (arg or latest)
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
    
    all_errors = []
    file_count = 0
    
    # Validate _index.json
    idx_path = data_dir / "_index.json"
    if idx_path.exists():
        data = json.loads(idx_path.read_text())
        errs = validate_json_schema(data, idx_schema, "_index.json")
        if errs:
            all_errors.extend(errs)
            print(f"  ❌ _index.json: {len(errs)} errors", file=sys.stderr)
        else:
            print(f"  ✅ _index.json", file=sys.stderr)
        
        # Check for fetch errors in index
        if data.get("errors"):
            for e in data["errors"]:
                msg = f"  ⚠️  Fetch error: {e['leaderboard']}: {e['error']}"
                print(msg, file=sys.stderr)
                all_errors.append(msg)
    else:
        all_errors.append("Missing _index.json")
        print(f"  ❌ Missing _index.json", file=sys.stderr)
    
    # Validate each leaderboard JSON
    for fp in sorted(data_dir.glob("*.json")):
        if fp.name.startswith("_"):
            continue
        file_count += 1
        data = json.loads(fp.read_text())
        errs = validate_json_schema(data, lb_schema, fp.name)
        
        # Additional checks
        if "meta" in data and "models" in data:
            declared = data["meta"].get("model_count", 0)
            actual = len(data["models"])
            if declared != actual:
                errs.append(f"model_count mismatch: meta says {declared}, actual {actual}")
            
            # Check ranks are sequential
            ranks = [m["rank"] for m in data["models"]]
            if ranks != list(range(1, len(ranks) + 1)):
                errs.append(f"ranks not sequential 1..{len(ranks)}")
        
        if errs:
            all_errors.extend(errs)
            print(f"  ❌ {fp.name}: {len(errs)} errors", file=sys.stderr)
            for e in errs:
                print(f"     {e}", file=sys.stderr)
        else:
            print(f"  ✅ {fp.name}", file=sys.stderr)
    
    if file_count == 0:
        all_errors.append("No leaderboard JSON files found")
    
    print(f"\n{file_count} files validated, {len(all_errors)} errors", file=sys.stderr)
    
    if all_errors:
        sys.exit(1)
    

if __name__ == "__main__":
    main()
