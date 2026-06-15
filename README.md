# Facebook Reels → Telegram Bot

Monitors a public Facebook Reels page every minute, replaces video audio with
custom background music, then sends the result to a Telegram channel.

> **Legal notice** – Only process content you own or have explicit permission
> to redistribute. This tool does not log in or bypass any security system.

---

## Folder Structure

```
king/
├── main.py              # entry point / poll loop
├── config.py            # env-var configuration
├── logger.py            # rotating log setup
├── database.py          # SQLite reel tracker
├── scraper.py           # Playwright Facebook scraper
├── downloader.py        # yt-dlp wrapper
├── processor.py         # FFmpeg audio-swap
├── telegram_sender.py   # Telegram Bot API uploader
├── requirements.txt
├── Procfile
├── railway.json
├── .env.example
├── music/               # ← put your .mp3 / .m4a files here
├── downloads/           # raw downloaded reels (auto-cleaned)
├── output/              # processed videos (auto-cleaned)
└── logs/
    └── app.log
```

---

## Local Setup

### Prerequisites
- Python 3.12
- FFmpeg installed and on `PATH`  
  - Windows: `winget install Gyan.FFmpeg`  
  - Linux/macOS: `sudo apt install ffmpeg` / `brew install ffmpeg`

### Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium --with-deps
```

### Configure

```bash
cp .env.example .env
# edit .env – fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID
```

### Add Background Music

Drop one or more `.mp3` / `.m4a` / `.wav` files into the `music/` folder.
A random track is chosen for each reel.

### Run

```bash
python main.py
```

---

## Railway Deployment

### 1 – Push to GitHub

```bash
git init
git add .
git commit -m "initial commit"
gh repo create king --private --source=. --push
```

### 2 – Create Railway project

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Select your repo.

### 3 – Set Environment Variables

In the Railway dashboard → **Variables** tab, add every key from `.env.example`
with your real values.

### 4 – Add a Volume (persistent SQLite + music)

Railway → **Add Service** → **Volume** → mount at `/app`.  
Upload your music files to `/app/music/` via the Railway shell or a startup script.

### 5 – Deploy

Railway auto-deploys on every `git push`.  
The `railway.json` restart policy retries on failure automatically.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | *(required)* | BotFather token |
| `TELEGRAM_CHANNEL_ID` | *(required)* | `@channel` or numeric ID |
| `FACEBOOK_REELS_URL` | see .env.example | Target public page |
| `CHECK_INTERVAL_SECONDS` | `60` | Poll frequency |
| `PLAYWRIGHT_HEADLESS` | `true` | Run browser headless |
| `MAX_SCROLL_ROUNDS` | `5` | Page scroll depth |
| `YTDLP_RATE_LIMIT` | `500K` | Download speed cap |
| `FFMPEG_THREADS` | `2` | FFmpeg thread count |
| `TELEGRAM_RETRIES` | `3` | Upload retry attempts |

---

## How It Works

```
Every CHECK_INTERVAL_SECONDS
  └─ scraper.fetch_reels()          # Playwright scrolls the public page
       └─ for each NEW reel_id
            ├─ downloader.get_video_info()   # metadata
            ├─ downloader.download_reel()    # yt-dlp → downloads/
            ├─ processor.process_video()     # FFmpeg swap audio → output/
            ├─ telegram_sender.send_video()  # upload to channel
            └─ cleanup temp files
```
