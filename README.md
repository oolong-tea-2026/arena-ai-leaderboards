# 📊 Arena AI Leaderboards — Daily Snapshots

[![Daily Fetch](https://github.com/oolong-tea-2026/arena-ai-leaderboards/actions/workflows/fetch.yml/badge.svg)](https://github.com/oolong-tea-2026/arena-ai-leaderboards/actions/workflows/fetch.yml)
![Leaderboards](https://img.shields.io/badge/leaderboards-10-blue)
![Models](https://img.shields.io/badge/models-300%2B-green)
![Updated](https://img.shields.io/badge/updated-daily-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

**Auto-updated daily snapshots of every [Arena AI](https://arena.ai/leaderboard/) (formerly LMSYS Chatbot Arena) leaderboard in structured JSON.**

Arena AI doesn't provide a public API. This repo gives you **stable, machine-readable data with full history** — updated automatically via GitHub Actions.

## 🏆 Today's Top Models

> Data auto-fetched daily. See [`data/latest.json`](data/latest.json) for the current snapshot.

### LLM (Text)
| Rank | Model | Vendor | Score |
|------|-------|--------|-------|
| 🥇 | claude-opus-4-6-thinking | Anthropic | 1502 |
| 🥈 | claude-opus-4-6 | Anthropic | 1501 |
| 🥉 | gemini-3.1-pro-preview | Google | 1493 |
| 4 | grok-4.20-beta1 | xAI | 1492 |
| 5 | gemini-3-pro | Google | 1486 |

### Text-to-Video
| Rank | Model | Vendor | Score |
|------|-------|--------|-------|
| 🥇 | veo-3.1-audio-1080p | Google | 1381 |
| 🥈 | veo-3.1-fast-audio-1080p | Google | 1378 |
| 🥉 | veo-3.1-audio | Google | 1371 |
| 4 | sora-2-pro | OpenAI | 1367 |
| 5 | veo-3.1-fast-audio | Google | 1366 |

*...and 8 more leaderboards: Code, Vision, Document, Image Edit, Image-to-Video, Text-to-Image, Search, Video Edit*

## 📁 Data Structure

```
data/
  latest.json              # → points to the newest snapshot
  2026-03-21/
    _index.json            # Run metadata + per-category stats
    text.json              # LLM leaderboard
    code.json              # Code generation
    vision.json            # Vision models
    text-to-video.json     # Video generation
    text-to-image.json     # Image generation
    image-to-video.json    # Image animation
    image-edit.json        # Image editing
    document.json          # Document understanding
    search.json            # Search/RAG
    video-edit.json        # Video editing
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

## 🤖 How It Works

1. **GitHub Actions** runs daily at ~01:37 UTC
2. **Auto-discovers** all leaderboard categories from [arena.ai/leaderboard](https://arena.ai/leaderboard/) (no hardcoded list)
3. **Fetches** full model rankings via [Jina Reader](https://jina.ai/reader/) (markdown extraction)
4. **Parses** with Azure OpenAI into structured JSON
5. **Validates** against JSON Schema
6. **Commits** to `data/{YYYY-MM-DD}/`

New categories added by Arena AI are picked up automatically.

## 💡 Why This Exists

- **Arena AI has no public API** — scraping their frontend is fragile
- **No historical data** — the website only shows current rankings
- **This repo provides**: stable JSON format, daily snapshots, full history, schema validation
- **Use cases**: research, model comparison dashboards, trend analysis, automated monitoring

## 🌟 10 Leaderboard Categories

| Category | Models | Description |
|----------|--------|-------------|
| Text | 67 | LLM chat (GPT, Claude, Gemini, ...) |
| Code | 55 | Code generation & completion |
| Vision | 30 | Multimodal vision understanding |
| Text-to-Image | 50 | Image generation (DALL-E, Midjourney, ...) |
| Text-to-Video | 37 | Video generation (Sora, Veo, Kling, ...) |
| Image-to-Video | 37 | Image animation |
| Image Edit | 39 | Image editing & inpainting |
| Document | 13 | Document understanding |
| Search | 22 | Search & RAG |
| Video Edit | 4 | Video editing |

## 📜 License

MIT — see [LICENSE](LICENSE).

Data sourced from [arena.ai](https://arena.ai). This repo provides structured access to publicly available leaderboard data.

---

**⭐ Star this repo** to get daily updates in your GitHub feed!
