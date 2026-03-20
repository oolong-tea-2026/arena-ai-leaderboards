# arena-ai-leaderboards

Daily snapshots of [arena.ai](https://arena.ai/leaderboard/) leaderboard data in structured JSON.

Arena.ai doesn't provide a public API, and its frontend format changes frequently. This repo provides a stable, machine-readable JSON data source updated daily via GitHub Actions.

## Leaderboards

Leaderboard categories are **discovered automatically** from the [overview page](https://arena.ai/leaderboard/) — no hardcoded list. When arena.ai adds or removes a category, the scraper picks it up automatically.

## Data Structure

```
data/
  latest.json              # Points to the most recent snapshot date
  2026-03-19/
    _index.json            # Run summary (date, fetched_at, per-category model counts, errors)
    text.json
    code.json
    text-to-video.json
    ...
```

### JSON Schema (unified across all leaderboards)

See `schemas/leaderboard.json` and `schemas/index.json` for formal definitions.

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
| `license` | `"proprietary"` \| `"open"` \| null | License category |
| `score` | int \| null | ELO/Arena score |
| `ci` | int \| null | Confidence interval (±) |
| `votes` | int \| null | Total vote count |

## License

Data sourced from [arena.ai](https://arena.ai). This repo provides structured access to publicly available leaderboard data.
