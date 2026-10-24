"""Tiny JSON file remembering which stories were already sent."""
import json
import time
from pathlib import Path

from . import config


class SeenStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.is_new_file = not self.path.exists()
        self._data: dict[str, int] = {}
        if not self.is_new_file:
            try:
                self._data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                self._data = {}
        self._prune()

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def add(self, key: str) -> None:
        self._data[key] = int(time.time())

    def _prune(self) -> None:
        cutoff = time.time() - config.SEEN_TTL_DAYS * 86400
        self._data = {k: t for k, t in self._data.items() if t >= cutoff}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2, sort_keys=True))
