# arena-ai-leaderboards

Daily snapshots of [arena.ai](https://arena.ai/leaderboard/) leaderboard data in structured JSON.

Arena.ai doesn't provide a public API, and its frontend format changes frequently. This repo provides a stable, machine-readable JSON data source updated daily via GitHub Actions.

## Leaderboards

Leaderboard categories are **discovered automatically** from the [overview page](https://arena.ai/leaderboard/). Currently tracked:

Text · Code · Vision · Document · Text-to-Image · Image Edit · Search · Text-to-Video · Image-to-Video · Video Edit

## Data Structure

```
data/
  2026-03-19/              # Daily snapshot
    _index.json            # Summary + metadata
    text.json
    code.json
    text-to-video.json
    ...
  2026-03-20/
    ...
```

### JSON Schema (unified across all leaderboards)

```json
{
  "meta": {
    "leaderboard": "text-to-video",
    "source_url": "https://arena.ai/leaderboard/text-to-video",
    "fetched_at": "2026-03-19T12:00:00+00:00",
    "last_updated": "13 days ago",
    "model_count": 37
  },
  "models": [
    {
      "rank": 1,
      "model": "veo-3.1-audio-1080p",
      "vendor": "Google",
      "license": "proprietary",
      "score": 1381,
      "ci": 8,
      "votes": 5537
    }
  ]
}
```

### Model Fields

| Field | Type | Description |
|---|---|---|
| `rank` | int | Position in leaderboard |
| `model` | string | Model name as shown on arena.ai |
| `vendor` | string \| null | Organization (Google, OpenAI, Anthropic, ...) |
| `license` | string \| null | `"proprietary"` or `"open"` |
| `score` | int | ELO/Arena score |
| `ci` | int \| null | Confidence interval (±) |
| `votes` | int | Total vote count |

## How It Works

1. GitHub Actions runs daily at 08:00 UTC
2. Overview page is scraped to discover all leaderboard categories
3. [Jina Reader](https://jina.ai/reader/) fetches each leaderboard page as clean text
4. LLM (Azure OpenAI) parses text into structured JSON
5. JSON validation ensures data integrity
6. Results committed to the repo

## Usage

Fetch the latest text-to-video leaderboard:
```bash
# Find the latest date
LATEST=$(ls -d data/2026-* | sort | tail -1)
curl -s "https://raw.githubusercontent.com/oolong-tea-2026/arena-ai-leaderboards/main/$LATEST/text-to-video.json" | jq '.models[:5]'
```

## License

Data sourced from [arena.ai](https://arena.ai). This repo provides structured access to publicly available leaderboard data.
