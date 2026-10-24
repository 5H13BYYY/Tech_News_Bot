"""Entry point:  python -m bot.main [--dry-run] [--loop] [--digest]"""
import argparse
import logging
import sys
import time

from . import config
from .digest import maybe_send_digest, send_digest_now
from .sources import fetch_hacker_news, fetch_lobsters, fetch_techmeme
from .storage import SeenStore
from .telegram import format_story, send_message

log = logging.getLogger("news-bot")

# Order matters: earlier sources win when two report the same URL.
SOURCES = [("HN", fetch_hacker_news), ("Techmeme", fetch_techmeme)]
if config.LOBSTERS_ENABLED:
    SOURCES.append(("Lobsters", fetch_lobsters))

# Sources that were already running before per-source tracking existed.
LEGACY_SOURCES = ("HN", "Techmeme")


def passes_filters(title: str) -> bool:
    t = title.lower()
    if any(w.lower() in t for w in config.BLOCKLIST):
        return False
    if config.ALLOWLIST and not any(w.lower() in t for w in config.ALLOWLIST):
        return False
    return True


def collect() -> dict:
    """Fetch every source. One failing source is OK; it is simply left out."""
    result = {}
    for name, fetch in SOURCES:
        try:
            result[name] = fetch()
        except Exception as exc:
            log.warning("%s failed: %s", name, exc)
    return result


def run_once(dry_run: bool = False) -> None:
    store = SeenStore(config.DATA_FILE)
    by_source = collect()

    if store.is_new_file and not any(by_source.values()):
        log.warning("First run but no stories fetched; will retry next time.")
        return

    # Upgrading an existing install: HN and Techmeme were already being tracked.
    if not store.is_new_file:
        for name in LEGACY_SOURCES:
            if f"source:{name}" not in store:
                store.add(f"source:{name}")

    # A source seen for the first time is recorded silently, so a new source
    # (or a fresh install) never floods you with the current front page.
    for name in [n for n in by_source if f"source:{n}" not in store]:
        for s in by_source.pop(name):
            store.add(s.key)
        store.add(f"source:{name}")
        log.info("New source %s: marked current stories as seen, nothing sent.", name)

    stories = [s for items in by_source.values() for s in items]

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

        store.add(s.key)  # also dedupes the same URL coming from another source
        sent += 1

    maybe_send_digest(store, dry_run)

    if not dry_run:
        store.save()
    log.info("Done: %d new stories %s.", sent, "shown" if dry_run else "sent")


def main() -> int:
    parser = argparse.ArgumentParser(description="Personal tech news Telegram bot")
    parser.add_argument("--dry-run", action="store_true", help="print, don't send or save")
    parser.add_argument("--loop", action="store_true", help="keep running forever")
    parser.add_argument("--digest", action="store_true", help="send the morning digest now and exit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.dry_run and not (config.TELEGRAM_TOKEN and config.TELEGRAM_CHAT_ID):
        log.error("Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID (see .env.example).")
        return 1

    if args.digest:
        send_digest_now(args.dry_run)
        return 0

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
