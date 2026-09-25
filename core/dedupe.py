"""Duplicate protection.

Replaces the old posted_*.txt files with one file: data/seen.json.
An item is remembered by a hash of its normalised title AND by a hash of
its link, so the same story under a slightly different headline is caught.

Items are only marked AFTER they were published (or deliberately rejected),
so a failed AI call never makes a job disappear forever.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from . import config, notify


def normalize(title):
    """Lower-case, drop ' - Publisher' suffix and punctuation."""
    t = re.sub(r"\s+-\s+[^-]{2,60}$", "", title or "")
    t = re.sub(r"[^a-z0-9\u0600-\u06FF]+", " ", t.lower())
    return t.strip()


def _hash(prefix, value):
    return prefix + hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def _keys(title, link):
    keys = []
    norm = normalize(title)
    if norm:
        keys.append(_hash("t:", norm))
    if link:
        keys.append(_hash("u:", link))
    return keys


class SeenStore:
    def __init__(self, path=None):
        self.path = Path(path or config.SEEN_FILE)
        self.data = {"version": 1, "imported": [], "items": {}}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as e:
                notify.log("SYSTEM", "WARN", f"Could not read {self.path}, starting fresh: {e}")
        self.data.setdefault("imported", [])
        self.data.setdefault("items", {})

    def is_seen(self, title, link=""):
        items = self.data["items"]
        return any(k in items for k in _keys(title, link))

    def mark(self, title, link, status, niche_name):
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for key in _keys(title, link):
            self.data["items"][key] = {
                "s": status, "n": niche_name, "t": (title or "")[:90], "at": stamp,
            }
        self.save()

    def import_legacy(self, niche):
        """One-time import of your old posted_*.txt so old items are not reposted."""
        if niche.name in self.data["imported"]:
            return
        legacy = Path(niche.legacy_file)
        count = 0
        if legacy.exists():
            for line in legacy.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line:
                    for key in _keys(line, ""):
                        self.data["items"].setdefault(
                            key, {"s": "legacy", "n": niche.name, "t": line[:90], "at": ""}
                        )
                    count += 1
        self.data["imported"].append(niche.name)
        self.save()
        notify.log(niche.label, "INFO", f"Imported {count} old titles from {niche.legacy_file}")

    def save(self):
        items = self.data["items"]
        if len(items) > config.SEEN_LIMIT:
            # dicts keep insertion order: drop the oldest entries
            for key in list(items)[: len(items) - config.SEEN_LIMIT]:
                del items[key]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.path)