"""Picks an article image.

Order: (optional) source image -> Unsplash (needs UNSPLASH_ACCESS_KEY) -> Pollinations AI image.
Returns (image_url, credit_html). credit_html is an attribution line to show under the article.
"""
import hashlib
import urllib.parse

import requests

from . import config, notify
from .textutil import esc


def _seed(title):
    return int(hashlib.sha1(title.encode("utf-8")).hexdigest()[:6], 16)


def _unsplash(query, seed):
    if not config.UNSPLASH_ACCESS_KEY:
        return "", ""
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 15, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {config.UNSPLASH_ACCESS_KEY}"},
            timeout=config.REQUEST_TIMEOUT,
        )
        results = resp.json().get("results", []) if resp.status_code == 200 else []
        if not results:
            return "", ""
        photo = results[seed % len(results)]
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


def pick(niche, candidate):
    if config.USE_SOURCE_IMAGES and candidate.image_url:
        return candidate.image_url, ""
    seed = _seed(candidate.title)
    url, credit = _unsplash(niche.image_query, seed)
    if url:
        return url, credit
    return _pollinations(niche, candidate.title, seed), ""