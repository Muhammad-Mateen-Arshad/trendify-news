"""Picks an article image.

Order per attempt: Openverse (no API key needed at all - real, Creative
Commons photos, used first so there's nothing to sign up for or that can
get "paused") -> Pexels (if you have a key) -> Unsplash (if you have a
key) -> (optional) the source article's own image -> Pollinations AI
image, so the site never ends up with no image at all.

For each candidate source, two queries are tried: a SPECIFIC one built
from the article's own title (so the photo actually relates to that
article), then the niche's GENERIC query as a safety net if the specific
search comes back empty. A small per-niche history file remembers recent
photo ids so the same photo does not keep repeating.
"""
import json
import random
import re
import urllib.parse
from pathlib import Path

import requests

from . import config, notify
from .textutil import esc

USED_IMAGES_FILE = Path("data/used_images.json")
USED_IMAGES_LIMIT = 400  # remembered photo ids per niche

_STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is",
    "are", "be", "as", "by", "with", "from", "into", "over", "amid", "after",
    "before", "this", "that", "these", "those", "its", "their", "his", "her",
    "new", "set", "says", "say", "said", "claims", "could", "would", "may",
    "will", "shall", "has", "have", "had", "not", "no", "yes", "who", "what",
    "when", "where", "why", "how", "but", "than", "then", "also", "more",
}


def _seed(title):
    return abs(hash(title)) % 1000


def _keywords(title, limit=4):
    """Pull a few meaningful words out of a title for a specific image search."""
    words = re.findall(r"[A-Za-z]+", title or "")
    out = []
    for w in words:
        if w.lower() in _STOPWORDS or len(w) < 3:
            continue
        if w not in out:
            out.append(w)
        if len(out) >= limit:
            break
    return out


# ------------------------------------------------------------------ used-image memory
def _load_used():
    try:
        return json.loads(USED_IMAGES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _mark_used(niche_name, photo_id, used):
    ids = used.setdefault(niche_name, [])
    ids.append(photo_id)
    used[niche_name] = ids[-USED_IMAGES_LIMIT:]
    try:
        USED_IMAGES_FILE.parent.mkdir(parents=True, exist_ok=True)
        USED_IMAGES_FILE.write_text(json.dumps(used, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        notify.log("IMAGES", "WARN", f"Could not save used-images store: {e}")


def _choose_fresh(photos, used_ids, prefix, id_key):
    """Prefer a photo whose id hasn't been used recently; fall back to any."""
    fresh = [p for p in photos if f"{prefix}:{p[id_key]}" not in used_ids]
    return random.choice(fresh or photos)


# ------------------------------------------------------------------ Openverse (primary - no key needed)
def _openverse_search(query, page):
    resp = requests.get(
        "https://api.openverse.org/v1/images/",
        params={
            "q": query,
            "page_size": 20,
            "page": page,
            "license_type": "commercial",   # safe for an ad-monetized site
            "category": "photograph",       # real photos, not illustrations/vectors
            "mature_content": "false",
        },
        timeout=config.REQUEST_TIMEOUT,
    )
    return resp.json().get("results", []) if resp.status_code == 200 else []


def _openverse(query, used_ids):
    if not query:
        return "", "", ""
    try:
        photos = _openverse_search(query, random.randint(1, 5))
        if not photos:
            photos = _openverse_search(query, 1)
        if not photos:
            return "", "", ""
        photo = _choose_fresh(photos, used_ids, "ov", "id")
        creator = photo.get("creator") or "an Openverse contributor"
        landing = photo.get("foreign_landing_url") or photo.get("url")
        credit = (
            f'Photo by {esc(creator)} via '
            f'<a href="{esc(landing)}" target="_blank" rel="noopener">Openverse</a>'
        )
        return photo["url"], credit, f"ov:{photo['id']}"
    except Exception as e:
        notify.log("IMAGES", "WARN", f"Openverse failed: {e}")
        return "", "", ""


# ------------------------------------------------------------------ Pexels (if you have a key)
def _pexels_search(query, page):
    resp = requests.get(
        "https://api.pexels.com/v1/search",
        params={"query": query, "per_page": 20, "orientation": "landscape", "page": page},
        headers={"Authorization": config.PEXELS_API_KEY},
        timeout=config.REQUEST_TIMEOUT,
    )
    return resp.json().get("photos", []) if resp.status_code == 200 else []


def _pexels(query, used_ids):
    if not config.PEXELS_API_KEY or not query:
        return "", "", ""
    try:
        photos = _pexels_search(query, random.randint(1, 5))
        if not photos:
            photos = _pexels_search(query, 1)
        if not photos:
            return "", "", ""
        photo = _choose_fresh(photos, used_ids, "px", "id")
        credit = (
            f'Photo by <a href="{esc(photo["photographer_url"])}" target="_blank" rel="noopener">'
            f'{esc(photo["photographer"])}</a> on '
            f'<a href="https://www.pexels.com" target="_blank" rel="noopener">Pexels</a>'
        )
        return photo["src"]["large"], credit, f"px:{photo['id']}"
    except Exception as e:
        notify.log("IMAGES", "WARN", f"Pexels failed: {e}")
        return "", "", ""


# ------------------------------------------------------------------ Unsplash (backup)
def _unsplash_search(query, page):
    resp = requests.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "per_page": 30, "orientation": "landscape", "page": page},
        headers={"Authorization": f"Client-ID {config.UNSPLASH_ACCESS_KEY}"},
        timeout=config.REQUEST_TIMEOUT,
    )
    return resp.json().get("results", []) if resp.status_code == 200 else []


def _unsplash(query, used_ids):
    if not config.UNSPLASH_ACCESS_KEY or not query:
        return "", "", ""
    try:
        photos = _unsplash_search(query, random.randint(1, 5))
        if not photos:
            photos = _unsplash_search(query, 1)
        if not photos:
            return "", "", ""
        photo = _choose_fresh(photos, used_ids, "us", "id")
        user = photo.get("user", {})
        profile = user.get("links", {}).get("html", "https://unsplash.com")
        credit = (
            f'Photo by <a href="{esc(profile)}?utm_source=trendify&amp;utm_medium=referral" '
            f'target="_blank" rel="noopener">{esc(user.get("name", "Unsplash contributor"))}</a> on '
            f'<a href="https://unsplash.com/?utm_source=trendify&amp;utm_medium=referral" '
            f'target="_blank" rel="noopener">Unsplash</a>'
        )
        return photo["urls"]["regular"], credit, f"us:{photo['id']}"
    except Exception as e:
        notify.log("IMAGES", "WARN", f"Unsplash failed: {e}")
        return "", "", ""


# ------------------------------------------------------------------ last-resort AI fallback
def _pollinations(niche, title, seed):
    subject = " ".join(title.split()[:8]) + " " if niche.image_from_title else ""
    prompt = urllib.parse.quote(f"{subject}{niche.image_style}")
    return f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=400&nologo=true&seed={seed % 1000}"


def _source_credit(source):
    return (
        f'Image via <a href="{esc(source.link)}" target="_blank" rel="noopener">'
        f"{esc(source.publisher)}</a>"
    )


# ------------------------------------------------------------------ main entry point
def pick(niche, candidate, source=None):
    used = _load_used()
    niche_used = set(used.get(niche.name, []))

    specific = " ".join(_keywords(candidate.title))
    queries = [q for q in (specific, niche.image_query) if q]
    seen_queries = []
    for q in queries:
        if q not in seen_queries:
            seen_queries.append(q)

    for query in seen_queries:
        for fetch in (_openverse, _pexels, _unsplash):
            url, credit, photo_id = fetch(query, niche_used)
            if url:
                if photo_id:
                    _mark_used(niche.name, photo_id, used)
                return url, credit

    if config.USE_SOURCE_IMAGES:
        if source is not None and source.image_url:
            return source.image_url, _source_credit(source)
        if candidate.image_url:
            return candidate.image_url, ""

    seed = _seed(candidate.title)
    return _pollinations(niche, candidate.title, seed), ""