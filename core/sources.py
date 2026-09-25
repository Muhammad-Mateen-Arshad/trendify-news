"""Reads feeds, finds the real article link and fetches the source text.

The AI is only allowed to write from this source text, which is what stops
it from inventing salaries, deadlines and qualifications.
"""
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urlparse
from functools import lru_cache

import feedparser
import requests
from bs4 import BeautifulSoup

from . import config, notify
from .textutil import html_to_text

# Check for googlenewsdecoder once at module load
try:
    from googlenewsdecoder import gnewsdecoder
    HAS_GNEWS_DECODER = True
except ImportError:
    HAS_GNEWS_DECODER = False

_session = requests.Session()
_session.headers.update({"User-Agent": config.USER_AGENT})


@dataclass
class Candidate:
    title: str
    summary: str
    link: str
    publisher: str
    image_url: str


@dataclass
class SourceInfo:
    link: str          # real article link (or the feed link if it could not be resolved)
    resolved: bool     # True when the link is the publisher's own page
    text: str          # text the AI may use
    publisher: str


def _get(url, timeout=None):
    return _session.get(url, timeout=timeout or config.REQUEST_TIMEOUT, allow_redirects=True)


# ------------------------------------------------------------------ feeds
def iter_candidates(niche):
    """Yield feed entries in priority order (first feed first)."""
    for feed_url in niche.feeds:
        try:
            resp = _get(feed_url)
            if resp.status_code != 200:
                notify.log(niche.label, "WARN", f"Feed HTTP {resp.status_code}: {feed_url[:90]}")
                continue
            feed = feedparser.parse(resp.content)
        except Exception as e:
            notify.log(niche.label, "WARN", f"Feed failed ({type(e).__name__}): {feed_url[:90]}")
            continue

        feed_title = (feed.feed.get("title") or "").strip() if getattr(feed, "feed", None) else ""
        for entry in feed.entries[: config.ITEMS_PER_FEED]:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            if not title or not link:
                continue
            publisher = ""
            source = entry.get("source")
            if source:
                publisher = (source.get("title") or "").strip()
            publisher = publisher or feed_title
            suffix = f" - {publisher}"
            if publisher and title.endswith(suffix):
                title = title[: -len(suffix)].strip()
            yield Candidate(
                title=title,
                summary=entry.get("summary", ""),
                link=link,
                publisher=publisher,
                image_url=_entry_image(entry) if config.USE_SOURCE_IMAGES else "",
            )


def _entry_image(entry):
    for key in ("media_content", "media_thumbnail"):
        items = entry.get(key)
        if items and items[0].get("url"):
            return items[0]["url"]
    for link in entry.get("links", []):
        if "image" in link.get("type", ""):
            return link.get("href", "")
    return ""


# ------------------------------------------------------------------ links
def resolve_link(link):
    """Google News links point to Google, not to the publisher. Try to find the real URL."""
    if "news.google.com" not in link:
        return link

    # Attempt 1: gnewsdecoder
    if HAS_GNEWS_DECODER:
        try:
            result = gnewsdecoder(link, interval=1)
            if result.get("status") and result.get("decoded_url"):
                return result["decoded_url"]
        except Exception:
            pass

    # Attempt 2: HTML meta refresh fallback
    try:
        resp = _get(link)
        if "news.google.com" not in resp.url:
            return resp.url
            
        soup = BeautifulSoup(resp.content, "html.parser")
        meta = soup.find("meta", attrs={"http-equiv": lambda x: x and x.lower() == "refresh"})
        if meta and meta.get("content"):
            content = meta["content"]
            if "url=" in content.lower():
                actual_url = content.lower().split("url=")[-1].strip("'\"")
                if actual_url:
                    return actual_url
    except Exception:
        pass
        
    return link


@lru_cache(maxsize=1000)
def _get_robot_parser(base_url):
    """Cached helper to fetch and parse robots.txt for a given base domain."""
    parser = urllib.robotparser.RobotFileParser()
    try:
        resp = _get(base_url + "/robots.txt", timeout=8)
        if resp.status_code == 200:
            parser.parse(resp.text.splitlines())
        elif resp.status_code in (401, 403):
            # Parse a generic rule that blocks all access instead of using undocumented attributes
            parser.parse(["User-agent: *", "Disallow: /"])
    except Exception:
        pass
    return parser


def robots_allows(url):
    """Respect robots.txt before downloading a page."""
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    parser = _get_robot_parser(base)
    return parser.can_fetch(config.ROBOTS_TOKEN, url)


# ------------------------------------------------------------------ page text
def extract_text(url):
    """Main readable text of a page (paragraphs and list items), or '' if not allowed / not possible."""
    try:
        if not robots_allows(url):
            return ""
        resp = _get(url)
        if resp.status_code != 200 or "html" not in resp.headers.get("Content-Type", "").lower():
            return ""
        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "iframe"]):
            tag.decompose()
        container = soup.find("article") or soup.find("main") or soup.body or soup
        parts = [p.get_text(" ", strip=True) for p in container.find_all(["p", "li"])]
        text = "\n".join(p for p in parts if len(p) > 40)
        return text[: config.SOURCE_TEXT_LIMIT]
    except Exception:
        return ""


def gather(candidate):
    """Resolve the link and collect the text the AI will be allowed to use."""
    link = resolve_link(candidate.link)
    resolved = "news.google.com" not in link
    page_text = extract_text(link) if resolved else ""
    summary = html_to_text(candidate.summary)
    
    if len(page_text) >= len(summary):
        text = page_text
    else:
        text = (summary + "\n" + page_text).strip()
        
    publisher = candidate.publisher or (urlparse(link).netloc.replace("www.", "") if resolved else "the source")
    return SourceInfo(link=link, resolved=resolved, text=text[: config.SOURCE_TEXT_LIMIT], publisher=publisher)