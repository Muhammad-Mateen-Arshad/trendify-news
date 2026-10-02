"""Reads feeds, finds the real article link and fetches the source text.

The AI is only allowed to write from this source text, which is what stops
it from inventing salaries, deadlines and qualifications.
"""
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from . import config, notify
from .textutil import html_to_text

_session = requests.Session()
_session.headers.update({"User-Agent": config.USER_AGENT})
_robots_cache = {}


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
    image_url: str = ""  # the publisher's own social-share image (og:image), if found


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
    try:
        from googlenewsdecoder import gnewsdecoder

        result = gnewsdecoder(link, interval=1)
        if result.get("status") and result.get("decoded_url"):
            return result["decoded_url"]
        notify.log("SOURCES", "WARN", f"gnewsdecoder could not decode: {link[:90]}")
    except ImportError:
        notify.log("SOURCES", "ERROR", "googlenewsdecoder is not installed - Google News links cannot be resolved")
    except Exception as e:
        notify.log("SOURCES", "WARN", f"gnewsdecoder failed ({type(e).__name__}): {link[:90]}")
    try:
        resp = _get(link)
        if "news.google.com" not in resp.url:
            return resp.url
    except Exception:
        pass
    return link


def robots_allows(url):
    """Respect robots.txt before downloading a page."""
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    parser = _robots_cache.get(base)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        try:
            resp = _get(base + "/robots.txt", timeout=8)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            elif resp.status_code in (401, 403):
                parser.disallow_all = True
            else:
                parser.allow_all = True
        except Exception:
            parser.allow_all = True
        parser.modified()
        _robots_cache[base] = parser
    return parser.can_fetch(config.ROBOTS_TOKEN, url)


# ------------------------------------------------------------------ page text + image
def _meta_image(soup, base_url):
    """The image the publisher itself uses when the page is shared on social media."""
    for attrs in (
        {"property": "og:image:secure_url"},
        {"property": "og:image"},
        {"name": "twitter:image"},
        {"name": "twitter:image:src"},
    ):
        tag = soup.find("meta", attrs=attrs)
        content = tag.get("content", "").strip() if tag else ""
        if content:
            return urljoin(base_url, content)
    return ""


def extract_page(url):
    """Main readable text (paragraphs and list items) and the page's share
    image, in one fetch. Returns ("", "") if not allowed or not possible."""
    try:
        if not robots_allows(url):
            return "", ""
        resp = _get(url)
        if resp.status_code != 200 or "html" not in resp.headers.get("Content-Type", "").lower():
            return "", ""
        soup = BeautifulSoup(resp.content, "html.parser")
        image_url = _meta_image(soup, url)
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "iframe"]):
            tag.decompose()
        container = soup.find("article") or soup.find("main") or soup.body or soup
        parts = [p.get_text(" ", strip=True) for p in container.find_all(["p", "li"])]
        text = "\n".join(p for p in parts if len(p) > 40)
        return text[: config.SOURCE_TEXT_LIMIT], image_url
    except Exception:
        return "", ""


def gather(candidate):
    """Resolve the link and collect the text (and image) the AI / publisher is allowed to use."""
    link = resolve_link(candidate.link)
    resolved = "news.google.com" not in link
    page_text, page_image = extract_page(link) if resolved else ("", "")
    if resolved and not page_text:
        notify.log("SOURCES", "WARN", f"Resolved but could not extract page text: {link[:90]}")
    summary = html_to_text(candidate.summary)
    if len(page_text) >= len(summary):
        text = page_text
    else:
        text = (summary + "\n" + page_text).strip()
    publisher = candidate.publisher or (urlparse(link).netloc.replace("www.", "") if resolved else "the source")
    return SourceInfo(
        link=link, resolved=resolved, text=text[: config.SOURCE_TEXT_LIMIT],
        publisher=publisher, image_url=page_image,
    )