# 📊 Arena AI Leaderboards — Daily Snapshots

[![Daily Fetch](https://github.com/oolong-tea-2026/arena-ai-leaderboards/actions/workflows/fetch.yml/badge.svg)](https://github.com/oolong-tea-2026/arena-ai-leaderboards/actions/workflows/fetch.yml)
![Leaderboards](https://img.shields.io/badge/leaderboards-10-blue)
![Models](https://img.shields.io/badge/models-300%2B-green)
![Updated](https://img.shields.io/badge/updated-daily-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

**Auto-updated daily snapshots of every [Arena AI](https://arena.ai/leaderboard/) (formerly LMSYS Chatbot Arena) leaderboard in structured JSON.**

Arena AI doesn't provide a public API. This repo gives you **stable, machine-readable data with historical tracking** — updated automatically via GitHub Actions.

## 📁 Data Structure

```
data/
  latest.json                # → points to the newest snapshot
  2026-03-21/
    _index.json              # Run metadata + per-category stats
    text.json                # Text & chat (LLM)
    code.json                # Code generation
    vision.json              # Image & multimodal understanding
    document.json            # PDF & document understanding
    text-to-image.json       # AI image generation
    image-edit.json          # Image editing
    search.json              # AI-powered search
    text-to-video.json       # AI video generation
    image-to-video.json      # Image-to-video generation
    video-edit.json          # Video editing
  2026-03-20/
    ...
```

## 🔌 Quick Access

### REST API (recommended)

Free, no auth needed. Hosted on **[api.wulong.dev](https://api.wulong.dev)**:

```bash
# List all leaderboards with model counts
curl https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboards

# Get a specific leaderboard (latest)
curl https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboard?name=text

# Get a specific date
curl https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboard?name=text-to-video&date=2026-03-21
```

### Raw GitHub JSON

```bash
# Latest snapshot pointer
curl https://raw.githubusercontent.com/oolong-tea-2026/arena-ai-leaderboards/main/data/latest.json

# Today's LLM leaderboard
curl https://raw.githubusercontent.com/oolong-tea-2026/arena-ai-leaderboards/main/data/2026-03-21/text.json
```

### Python

```python
import requests

# Via API
text = requests.get(
    "https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboard?name=text"
).json()

for m in text["models"][:10]:
    print(f"#{m['rank']} {m['model']} ({m['vendor']}) — ELO {m['score']}±{m['ci']}")
```

## 📐 JSON Schema

Every leaderboard file follows a unified schema. See [`schemas/`](schemas/) for formal JSON Schema definitions.

```json
{
  "meta": {
    "leaderboard": "text-to-video",
    "source_url": "https://arena.ai/leaderboard/text-to-video",
    "fetched_at": "2026-03-21T05:12:05+00:00",
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

| Field | Type | Description |
|-------|------|-------------|
| `rank` | int | Position in leaderboard |
| `model` | string | Model name as shown on arena.ai |
| `vendor` | string \| null | Organization (Google, OpenAI, Anthropic, ...) |
| `license` | `"proprietary"` \| `"open"` \| null | License category |
| `score` | int \| null | Arena ELO score |
| `ci` | int \| null | 95% confidence interval (±) |
| `votes` | int \| null | Total vote count |

## 📜 License

MIT — see [LICENSE](LICENSE).

Data sourced from [arena.ai](https://arena.ai). This repo provides structured access to publicly available leaderboard data.

---

**⭐ Star this repo** to get daily updates in your GitHub feed!
