# arena-ai-leaderboards

Daily snapshots of [arena.ai](https://arena.ai/leaderboard/) leaderboard data in structured JSON.

Arena.ai doesn't provide a public API, and its frontend format changes frequently. This repo provides a stable, machine-readable JSON data source updated daily via GitHub Actions.

## Leaderboards Tracked

| Leaderboard | Category | Path |
|---|---|---|
| Text | LLM overall | `text` |
| Code | Programming | `code` |
| Vision | Multimodal vision | `vision` |
| Document | Document understanding | `document` |
| Text-to-Image | Image generation | `text-to-image` |
| Image Edit | Image editing | `image-edit` |
| Search | Search/RAG | `search` |
| Text-to-Video | Video generation | `text-to-video` |
| Image-to-Video | Image to video | `image-to-video` |
| Video Edit | Video editing | `video-edit` |

## Data Structure

```
data/
  latest/                    # Always the most recent snapshot
    text.json
    code.json
    vision.json
    ...
  history/                   # Daily archives
    2026-03-19/
      text.json
      code.json
      ...
```

### JSON Schema

Each leaderboard JSON file:

```json
{
  "leaderboard": "text",
  "source": "https://arena.ai/leaderboard/text",
  "fetched_at": "2026-03-19T12:00:00Z",
  "last_updated": "21 hours ago",
  "models": [
    {
      "rank": 1,
      "model": "claude-opus-4-6-thinking",
      "score": 1502,
      "votes": 11671
    }
  ]
}
```

## How It Works

1. GitHub Actions runs daily (cron)
2. [Jina Reader](https://jina.ai/reader/) fetches arena.ai pages as clean text
3. LLM (OpenAI) parses the text into structured JSON
4. JSON schema validation ensures data integrity
5. Results are committed to the repo

## Usage

Fetch the latest text leaderboard:
```bash
curl -s https://raw.githubusercontent.com/oolong-tea-2026/arena-ai-leaderboards/main/data/latest/text.json | jq '.models[:5]'
```

## License

Data sourced from [arena.ai](https://arena.ai). This repo provides structured access to publicly available leaderboard data.
