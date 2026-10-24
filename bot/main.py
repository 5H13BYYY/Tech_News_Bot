"""Entry point:  python -m bot.main [--dry-run] [--loop]"""
import argparse
import logging
import sys
import time

from . import config
from .sources import fetch_hacker_news, fetch_techmeme
from .storage import SeenStore
from .telegram import format_story, send_message

log = logging.getLogger("news-bot")


def passes_filters(title: str) -> bool:
    t = title.lower()
    if any(w.lower() in t for w in config.BLOCKLIST):
        return False
    if config.ALLOWLIST and not any(w.lower() in t for w in config.ALLOWLIST):
        return False
    return True


def collect():
    """HN first (primary), then Techmeme (secondary). One failing source is OK."""
    stories = []
    for fetch in (fetch_hacker_news, fetch_techmeme):
        try:
            stories.extend(fetch())
        except Exception as exc:
            log.warning("%s failed: %s", fetch.__name__, exc)
    return stories


def run_once(dry_run: bool = False) -> None:
    store = SeenStore(config.DATA_FILE)
    stories = collect()

    # First run: mark everything currently on the feeds as seen, send nothing.
    if store.is_new_file:
        if not stories:
            log.warning("First run but no stories fetched; will retry next time.")
            return
        for s in stories:
            store.add(s.key)
        if not dry_run:
            store.save()
        log.info("First run: marked %d stories as seen, nothing sent.", len(stories))
        return

    sent = 0
    for s in stories:
        if s.key in store:
            continue
        if not passes_filters(s.title):
            continue
        if sent >= config.MAX_MESSAGES_PER_RUN:
            break  # leftovers go out on the next run

        text = format_story(s)
        if dry_run:
            print(text, end="\n\n")
        else:
            try:
                send_message(text)
            except Exception as exc:
                log.error("Send failed (%s); stopping this run.", exc)
                break
            time.sleep(1)  # stay well under Telegram's rate limit

        store.add(s.key)  # also dedupes the same URL coming from the other source
        sent += 1

    if not dry_run:
        store.save()
    log.info("Done: %d new stories %s.", sent, "shown" if dry_run else "sent")


def main() -> int:
    parser = argparse.ArgumentParser(description="Personal tech news Telegram bot")
    parser.add_argument("--dry-run", action="store_true", help="print, don't send or save")
    parser.add_argument("--loop", action="store_true", help="keep running forever")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.dry_run and not (config.TELEGRAM_TOKEN and config.TELEGRAM_CHAT_ID):
        log.error("Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID (see .env.example).")
        return 1

    if args.loop:
        while True:
            try:
                run_once(args.dry_run)
            except Exception:
                log.exception("Run crashed; will retry.")
            time.sleep(config.LOOP_INTERVAL_SECONDS)
    run_once(args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
