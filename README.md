# tech-news-bot

Personal Telegram alerts from Hacker News (primary) and Techmeme (secondary).

## Setup
1. Create a bot with @BotFather, copy the token.
2. Message your bot once, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `chat.id`.
3. `cp .env.example .env` and fill in both values.
4. `pip install -r requirements.txt`

## Run
    python -m bot.main --dry-run   # preview, sends nothing
    python -m bot.main             # one check
    python -m bot.main --loop      # check every 10 min (VPS / always-on PC)

The first real run only records what's currently on the feeds; alerts start
with the next new story.

## GitHub Actions (free hosting)
Push the repo, add `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` under
Settings > Secrets and variables > Actions. The workflow runs every ~15 min
and commits `data/seen.json` back so nothing is sent twice.

## Tuning
Edit `bot/config.py`: points threshold, keyword allow/block lists,
max messages per run.
