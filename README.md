# arena-ai-leaderboards

Daily snapshots of [arena.ai](https://arena.ai/leaderboard/) leaderboard data in structured JSON.

Arena.ai doesn't provide a public API, and its frontend format changes frequently. This repo provides a stable, machine-readable JSON data source updated daily via GitHub Actions.

## Leaderboards

Leaderboard categories are **discovered automatically** from the [overview page](https://arena.ai/leaderboard/) — no hardcoded list. When arena.ai adds or removes a category, the scraper picks it up automatically.

## Data Structure

```
data/
  2026-03-19/              # Daily snapshot
    _index.json            # Summary + metadata
    text.json
    code.json
    text-to-video.json
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

## License

Data sourced from [arena.ai](https://arena.ai). This repo provides structured access to publicly available leaderboard data.
