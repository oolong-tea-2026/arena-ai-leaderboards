#!/usr/bin/env python3
"""
Fetch arena.ai leaderboard data using Jina Reader + LLM parsing.
Validates each result against JSON Schema before writing.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

from jsonschema import Draft202012Validator

JINA_READER_BASE = "https://r.jina.ai/"
ARENA_BASE = "https://arena.ai/leaderboard/"


def fetch_page(url: str, jina_api_key: str | None = None) -> str:
    """Fetch a page via Jina Reader and return markdown text."""
    reader_url = f"{JINA_READER_BASE}{url}"
    headers = {
        "Accept": "application/json",
        "X-Return-Format": "markdown",
        "User-Agent": "Mozilla/5.0 (compatible; arena-leaderboard-bot/1.0)",
    }
    if jina_api_key:
        headers["Authorization"] = f"Bearer {jina_api_key}"

    req = urllib.request.Request(reader_url, headers=headers)

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.URLError as e:
            print(f"  Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(5 * (attempt + 1))

    raise RuntimeError(f"Failed to fetch {url} after 3 attempts")


def discover_leaderboards(overview_text: str) -> list[tuple[str, str]]:
    """Extract leaderboard slugs from overview page links."""
    pattern = r'arena\.ai/leaderboard/([a-z][a-z0-9-]*)'
    slugs = sorted(set(re.findall(pattern, overview_text)))
    return [(s, s) for s in slugs]


SYSTEM_PROMPT = """You are a data extraction assistant. Extract the FULL leaderboard table from the provided text.

Return ONLY valid JSON with this exact structure:
{
  "last_updated": "string or null (e.g., '21 hours ago', '5 days ago')",
  "models": [
    {
      "rank": 1,
      "model": "model-name-exactly-as-shown",
      "vendor": "OpenAI",
      "license": "proprietary",
      "score": 1502,
      "ci": 8,
      "votes": 11671
    }
  ]
}

Rules:
- Extract ALL models in the leaderboard, every single row
- "rank": integer rank
- "model": exact model name string as displayed
- "vendor": organization/company name (e.g., "OpenAI", "Google", "Anthropic", "xAI", "Meta"). null if not shown
- "license": MUST be exactly "proprietary" or "open". Map any open-source license (MIT, Apache, etc.) to "open". null only if not shown
- "score": the ELO/Arena score as integer
- "ci": the confidence interval number (e.g., if shown as "±8" or "1502±8", extract 8). null if not shown
- "votes": vote count as integer. Remove commas
- If any field is missing or shows "-", use null
- Return raw JSON only, no markdown fences, no commentary"""


def _parse_llm_response(content: str) -> dict:
    """Clean and parse LLM JSON response."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    return json.loads(content)


def parse_with_azure(text: str, slug: str, api_key: str, endpoint: str,
                     deployment: str, api_version: str) -> dict:
    url = (f"{endpoint.rstrip('/')}/openai/deployments/{deployment}"
           f"/chat/completions?api-version={api_version}")
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f'Extract the "{slug}" leaderboard data:\n\n{text[:15000]}'}
        ],
        "temperature": 0,
        "max_tokens": 16000,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json", "api-key": api_key,
    }, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _parse_llm_response(data["choices"][0]["message"]["content"])


def parse_with_openai(text: str, slug: str, api_key: str) -> dict:
    payload = json.dumps({
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f'Extract the "{slug}" leaderboard data:\n\n{text[:15000]}'}
        ],
        "temperature": 0,
        "max_tokens": 16000,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _parse_llm_response(data["choices"][0]["message"]["content"])


def normalize_license(lic):
    """Normalize license to 'proprietary' | 'open' | None."""
    if not isinstance(lic, str):
        return None
    lic_lower = lic.lower()
    if lic_lower == "proprietary":
        return "proprietary"
    if lic_lower in ("open", "open source", "open-source"):
        return "open"
    if any(kw in lic_lower for kw in ("mit", "apache", "bsd", "gpl", "cc-", "community", "non-commercial")):
        return "open"
    return "open"  # default non-proprietary to open


def main():
    jina_key = os.environ.get("JINA_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    azure_key = os.environ.get("AZURE_OPENAI_KEY")
    azure_endpoint = os.environ.get("AZURE_ENDPOINT")
    azure_deployment = os.environ.get("AZURE_DEPLOYMENT", "gpt-4o")
    azure_api_version = os.environ.get("AZURE_API_VERSION", "2025-01-01-preview")

    use_azure = bool(azure_key and azure_endpoint)
    use_openai = bool(openai_key)

    if not (use_azure or use_openai):
        print("ERROR: Set OPENAI_API_KEY or AZURE_OPENAI_KEY + AZURE_ENDPOINT", file=sys.stderr)
        sys.exit(1)

    print(f"Using {'Azure OpenAI' if use_azure else 'OpenAI'}", file=sys.stderr)

    # Load schemas
    repo_root = Path(__file__).resolve().parent.parent
    schema_dir = repo_root / "schemas"
    lb_schema = json.loads((schema_dir / "leaderboard.json").read_text())
    idx_schema = json.loads((schema_dir / "index.json").read_text())
    lb_validator = Draft202012Validator(lb_schema)
    idx_validator = Draft202012Validator(idx_schema)

    # Discover leaderboards
    print("\nDiscovering leaderboards from overview...", file=sys.stderr)
    overview_text = fetch_page(ARENA_BASE, jina_key)
    leaderboards = discover_leaderboards(overview_text)
    print(f"Found {len(leaderboards)} leaderboards: {[s for s, _ in leaderboards]}", file=sys.stderr)

    if not leaderboards:
        print("ERROR: No leaderboards discovered", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    day_dir = repo_root / "data" / date_str
    day_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    errors = []

    for slug, url_path in leaderboards:
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"Processing: {slug}", file=sys.stderr)

        try:
            # 1. Fetch
            url = f"{ARENA_BASE}{url_path}"
            print(f"  Fetching {url}...", file=sys.stderr)
            text = fetch_page(url, jina_key)
            print(f"  Got {len(text)} chars", file=sys.stderr)

            # 2. Parse with LLM
            print(f"  Parsing with LLM...", file=sys.stderr)
            if use_azure:
                parsed = parse_with_azure(text, slug, azure_key, azure_endpoint,
                                          azure_deployment, azure_api_version)
            else:
                parsed = parse_with_openai(text, slug, openai_key)

            if not isinstance(parsed.get("models"), list) or len(parsed["models"]) == 0:
                raise ValueError("LLM returned no models")

            # 3. Build output + normalize
            output = {
                "meta": {
                    "leaderboard": slug,
                    "source_url": url,
                    "fetched_at": now.isoformat(),
                    "last_updated": parsed.get("last_updated"),
                    "model_count": len(parsed["models"]),
                },
                "models": parsed["models"],
            }

            for m in output["models"]:
                m.setdefault("rank", None)
                m.setdefault("model", None)
                m.setdefault("vendor", None)
                m.setdefault("score", None)
                m.setdefault("ci", None)
                m.setdefault("votes", None)
                m["license"] = normalize_license(m.get("license"))

            # 4. Schema validation
            print(f"  Validating schema...", file=sys.stderr)
            schema_errors = list(lb_validator.iter_errors(output))
            if schema_errors:
                err_msgs = [f"{e.json_path}: {e.message}" for e in schema_errors[:5]]
                raise ValueError(f"Schema validation failed: {'; '.join(err_msgs)}")

            print(f"  ✅ {len(parsed['models'])} models, schema valid", file=sys.stderr)

            # 5. Write
            fp = day_dir / f"{slug}.json"
            with open(fp, "w") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"  Wrote {fp}", file=sys.stderr)

            results[slug] = len(parsed["models"])
            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Error: {e}", file=sys.stderr)
            errors.append({"leaderboard": slug, "error": str(e)})

    # Write & validate index
    index = {
        "date": date_str,
        "fetched_at": now.isoformat(),
        "leaderboards": {slug: {"model_count": count} for slug, count in results.items()},
        "errors": errors,
    }
    idx_errors = list(idx_validator.iter_errors(index))
    if idx_errors:
        print(f"  ❌ Index schema invalid: {idx_errors[0].message}", file=sys.stderr)

    with open(day_dir / "_index.json", "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # Write latest.json pointer
    latest = {"date": date_str, "path": date_str}
    with open(repo_root / "data" / "latest.json", "w") as f:
        json.dump(latest, f, indent=2)
    print(f"\nUpdated data/latest.json → {date_str}", file=sys.stderr)

    # Summary
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"Done: {len(results)}/{len(leaderboards)} leaderboards → {day_dir}", file=sys.stderr)
    for slug, count in results.items():
        print(f"  {slug}: {count} models", file=sys.stderr)
    if errors:
        print(f"Errors: {len(errors)}", file=sys.stderr)
        for e in errors:
            print(f"  {e['leaderboard']}: {e['error']}", file=sys.stderr)
        sys.exit(1)

    if len(results) < len(leaderboards):
        print(f"FAIL: only {len(results)}/{len(leaderboards)} succeeded", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
