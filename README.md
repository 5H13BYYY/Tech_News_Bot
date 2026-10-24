# tech-news-bot

Personal Telegram alerts from Hacker News (primary), Techmeme (secondary)
and Lobsters (third), plus a morning digest.

## Setup
1. Create a bot with @BotFather, copy the token.
2. Message your bot once, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `chat.id`.
3. Copy `.env.example` to `.env` and fill in both values.
4. `pip install -r requirements.txt`

## Run
    python -m bot.main --dry-run   # preview, sends nothing
    python -m bot.main             # one check (alerts + digest if due)
    python -m bot.main --digest    # send the morning digest right now
    python -m bot.main --loop      # check every 10 min (VPS / always-on PC)

A new source (or a fresh install) is recorded silently on its first run, so
alerts only start with the next new story.

## Morning digest
Sent once per local day by the first run at or after `DIGEST_HOUR` (default 8,
in `TIMEZONE`): top HN front-page stories, the latest Techmeme items and the
hottest Lobsters stories.

## Topic tags
Each alert gets up to two tags (AI, Security, Funding, Crypto, Policy, Hardware,
Science, Dev, BigTech, General) chosen by keywords in the headline. Edit the word
lists in `bot/classify.py`; set `CLASSIFY_ENABLED = False` in `bot/config.py` to
turn it off. Tags are hashtags, so tapping one in Telegram lists every alert with it.

## GitHub Actions (free hosting)
Add `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` under
Settings > Secrets and variables > Actions, and set Workflow permissions to
read and write. The workflow runs every ~15 min and commits `data/seen.json`
back so nothing is sent twice. Run `git pull --rebase origin main` before
pushing from your PC.

## Tuning
Edit `bot/config.py`: thresholds, keyword lists, digest hour and sizes,
timezone, `LOBSTERS_ENABLED`.
