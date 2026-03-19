#!/usr/bin/env python3
"""
Fetch arena.ai leaderboard data using Jina Reader + LLM parsing.
Outputs structured JSON for each leaderboard category.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

# Leaderboard configs: (slug, url_path)
LEADERBOARDS = [
    ("text", "text"),
    ("code", "code"),
    ("vision", "vision"),
    ("document", "document"),
    ("text-to-image", "text-to-image"),
    ("image-edit", "image-edit"),
    ("search", "search"),
    ("text-to-video", "text-to-video"),
    ("image-to-video", "image-to-video"),
    ("video-edit", "video-edit"),
]

JINA_READER_BASE = "https://r.jina.ai/"
ARENA_BASE = "https://arena.ai/leaderboard/"


def fetch_page(url: str, jina_api_key: str | None = None) -> str:
    """Fetch a page via Jina Reader and return markdown text."""
    reader_url = f"{JINA_READER_BASE}{url}"
    headers = {"Accept": "text/plain"}
    if jina_api_key:
        headers["Authorization"] = f"Bearer {jina_api_key}"
    
    req = urllib.request.Request(reader_url, headers=headers)
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.URLError as e:
            print(f"  Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
    
    raise RuntimeError(f"Failed to fetch {url} after 3 attempts")


def parse_with_llm(text: str, leaderboard_slug: str, openai_api_key: str,
                   model: str = "gpt-4o", endpoint: str = "https://api.openai.com/v1",
                   extra_headers: dict | None = None) -> dict:
    """Use LLM to extract structured leaderboard data from text."""
    
    system_prompt = """You are a data extraction assistant. Extract leaderboard data from the provided text.

Return ONLY valid JSON with this exact structure:
{
  "last_updated": "string (e.g., '21 hours ago', '5 days ago')",
  "models": [
    {
      "rank": 1,
      "model": "model-name",
      "score": 1502,
      "votes": 11671
    }
  ]
}

Rules:
- Extract ALL models shown in the leaderboard, not just top 10
- "score" is the ELO/Arena score (integer)
- "votes" is the vote count (integer) 
- If score or votes contain commas, remove them
- If a field is missing or shows "-", use null
- Return raw JSON only, no markdown fences"""

    user_prompt = f"""Extract the "{leaderboard_slug}" leaderboard data from this text:

{text[:12000]}"""

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0,
        "max_tokens": 8000,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(
        f"{endpoint}/chat/completions",
        data=payload,
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    content = data["choices"][0]["message"]["content"].strip()
    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    
    return json.loads(content)


def validate(data: dict) -> bool:
    """Basic validation of parsed leaderboard data."""
    if "models" not in data:
        return False
    if not isinstance(data["models"], list):
        return False
    if len(data["models"]) == 0:
        return False
    
    for m in data["models"]:
        if "rank" not in m or "model" not in m:
            return False
    
    return True


def main():
    # Config from environment
    jina_key = os.environ.get("JINA_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    azure_key = os.environ.get("AZURE_OPENAI_KEY")
    azure_endpoint = os.environ.get("AZURE_ENDPOINT")
    azure_deployment = os.environ.get("AZURE_DEPLOYMENT", "gpt-4o")
    azure_api_version = os.environ.get("AZURE_API_VERSION", "2025-01-01-preview")
    
    # Determine LLM backend
    if azure_key and azure_endpoint:
        llm_endpoint = f"{azure_endpoint.rstrip('/')}/openai/deployments/{azure_deployment}"
        llm_key = azure_key
        llm_model = azure_deployment
        extra_headers = {"api-key": azure_key}
        # Azure uses api-key header, not Bearer
        llm_key = "placeholder"  # won't be used
        print("Using Azure OpenAI", file=sys.stderr)
    elif openai_key:
        llm_endpoint = "https://api.openai.com/v1"
        llm_key = openai_key
        llm_model = "gpt-4o"
        extra_headers = None
        print("Using OpenAI", file=sys.stderr)
    else:
        print("ERROR: Set OPENAI_API_KEY or AZURE_OPENAI_KEY + AZURE_ENDPOINT", file=sys.stderr)
        sys.exit(1)

    # Output dirs
    repo_root = Path(__file__).resolve().parent.parent
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    
    latest_dir = repo_root / "data" / "latest"
    history_dir = repo_root / "data" / "history" / date_str
    latest_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    errors = []

    for slug, url_path in LEADERBOARDS:
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"Processing: {slug}", file=sys.stderr)
        
        try:
            # Step 1: Fetch
            url = f"{ARENA_BASE}{url_path}"
            print(f"  Fetching {url}...", file=sys.stderr)
            text = fetch_page(url, jina_key)
            print(f"  Got {len(text)} chars", file=sys.stderr)
            
            # Step 2: Parse with LLM
            print(f"  Parsing with LLM...", file=sys.stderr)
            
            if azure_key and azure_endpoint:
                # Azure OpenAI path
                parsed = parse_with_azure(text, slug, azure_key, azure_endpoint, 
                                          azure_deployment, azure_api_version)
            else:
                parsed = parse_with_llm(text, slug, llm_key, llm_model, llm_endpoint, extra_headers)
            
            # Step 3: Validate
            if not validate(parsed):
                raise ValueError(f"Validation failed for {slug}")
            
            print(f"  ✅ Got {len(parsed['models'])} models", file=sys.stderr)

            # Step 4: Build output
            output = {
                "leaderboard": slug,
                "source": url,
                "fetched_at": now.isoformat(),
                "last_updated": parsed.get("last_updated"),
                "model_count": len(parsed["models"]),
                "models": parsed["models"],
            }

            # Write files
            for d in [latest_dir, history_dir]:
                fp = d / f"{slug}.json"
                with open(fp, "w") as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print(f"  Wrote {fp}", file=sys.stderr)
            
            results[slug] = len(parsed["models"])
            
            # Rate limit courtesy
            time.sleep(2)

        except Exception as e:
            print(f"  ❌ Error: {e}", file=sys.stderr)
            errors.append({"leaderboard": slug, "error": str(e)})

    # Summary
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"Done: {len(results)}/{len(LEADERBOARDS)} leaderboards", file=sys.stderr)
    for slug, count in results.items():
        print(f"  {slug}: {count} models", file=sys.stderr)
    if errors:
        print(f"Errors: {len(errors)}", file=sys.stderr)
        for e in errors:
            print(f"  {e['leaderboard']}: {e['error']}", file=sys.stderr)
        sys.exit(1)


def parse_with_azure(text: str, slug: str, api_key: str, endpoint: str,
                     deployment: str, api_version: str) -> dict:
    """Parse using Azure OpenAI API."""
    system_prompt = """You are a data extraction assistant. Extract leaderboard data from the provided text.

Return ONLY valid JSON with this exact structure:
{
  "last_updated": "string (e.g., '21 hours ago', '5 days ago')",
  "models": [
    {
      "rank": 1,
      "model": "model-name",
      "score": 1502,
      "votes": 11671
    }
  ]
}

Rules:
- Extract ALL models shown in the leaderboard, not just top 10
- "score" is the ELO/Arena score (integer)
- "votes" is the vote count (integer) 
- If score or votes contain commas, remove them
- If a field is missing or shows "-", use null
- Return raw JSON only, no markdown fences"""

    user_prompt = f"""Extract the "{slug}" leaderboard data from this text:

{text[:12000]}"""

    url = (f"{endpoint.rstrip('/')}/openai/deployments/{deployment}"
           f"/chat/completions?api-version={api_version}")
    
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0,
        "max_tokens": 8000,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    
    return json.loads(content)


if __name__ == "__main__":
    main()
