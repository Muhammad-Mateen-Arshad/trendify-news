"""Picks an article image.

Order: real image from the source article (og:image) -> Unsplash (needs
UNSPLASH_ACCESS_KEY) -> Pollinations AI image, so the site never ends up
with no image at all even when scraping fails.
Returns (image_url, credit_html). credit_html is an attribution line to show under the article.
"""
import hashlib
import json
import random
import urllib.parse
from pathlib import Path

import requests

from . import config, notify
from .textutil import esc


USED_IMAGES_FILE = Path("data/used_images.json")


def _load_used():
    try:
        if USED_IMAGES_FILE.exists():
            with open(USED_IMAGES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_used(data):
    try:
        USED_IMAGES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USED_IMAGES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def _was_used(niche_name, photo_id):
    data = _load_used()
    return photo_id in data.get(niche_name, [])


def _mark_used(niche_name, photo_id):
    data = _load_used()
    if niche_name not in data:
        data[niche_name] = []
    data[niche_name].append(photo_id)
    if len(data[niche_name]) > 300:
        data[niche_name] = data[niche_name][-300:]
    _save_used(data)


def _seed(title):
    return int(hashlib.sha1(title.encode("utf-8")).hexdigest()[:6], 16)


def _unsplash(query, niche_name):
    if not config.UNSPLASH_ACCESS_KEY:
        return "", ""
    try:
        page = random.randint(1, 15)

        def fetch(p):
            resp = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 30, "page": p, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {config.UNSPLASH_ACCESS_KEY}"},
                timeout=config.REQUEST_TIMEOUT,
            )
            return resp.json().get("results", []) if resp.status_code == 200 else []

        results = fetch(page)
        if not results and page != 1:
            results = fetch(1)

        if not results:
            return "", ""

        unused_results = [r for r in results if not _was_used(niche_name, r["id"])]
        if unused_results:
            photo = random.choice(unused_results)
        else:
            photo = random.choice(results)

        _mark_used(niche_name, photo["id"])

        user = photo.get("user", {})
        profile = user.get("links", {}).get("html", "https://unsplash.com")
        credit = (
            f'Photo by <a href="{esc(profile)}?utm_source=trendify&amp;utm_medium=referral" '
            f'target="_blank" rel="noopener">{esc(user.get("name", "Unsplash contributor"))}</a> on '
            f'<a href="https://unsplash.com/?utm_source=trendify&amp;utm_medium=referral" '
            f'target="_blank" rel="noopener">Unsplash</a>'
        )
        return photo["urls"]["regular"], credit
    except Exception as e:
        notify.log("IMAGES", "WARN", f"Unsplash failed: {e}")
        return "", ""


def _pollinations(niche, title, seed):
    subject = " ".join(title.split()[:8]) + " " if niche.image_from_title else ""
    prompt = urllib.parse.quote(f"{subject}{niche.image_style}")
    return f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=400&nologo=true&seed={seed % 1000}"


def _source_credit(source):
    return (
        f'Image via <a href="{esc(source.link)}" target="_blank" rel="noopener">'
        f"{esc(source.publisher)}</a>"
    )


def pick(niche, candidate, source=None):
    seed = _seed(candidate.title)
    url, credit = _unsplash(niche.image_query, niche.name)
    if url:
        return url, credit
    if config.USE_SOURCE_IMAGES:
        if source is not None and source.image_url:
            return source.image_url, _source_credit(source)
        if candidate.image_url:
            return candidate.image_url, ""
    return _pollinations(niche, candidate.title, seed), ""