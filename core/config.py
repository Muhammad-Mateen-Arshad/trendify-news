"""Central settings for all Trendify bots.

Importing this module also moves the working directory to the repo root,
so every relative path in the project (jobs/, data/, jobs.html ...) works
no matter where the script is started from.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

# ---------------------------------------------------------------- site
SITE_URL = (os.environ.get("SITE_URL") or "https://Muhammad-Mateen-Arshad.github.io/trendify-news").rstrip("/")
SITE_NAME = "Trendify Portal"
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL") or "@trendify_news_live"

# ---------------------------------------------------------------- AI
# Same model name you already use. Change it in one place (or via the
# GEMINI_MODEL environment variable) and all six bots follow.
MODEL_NAME = os.environ.get("GEMINI_MODEL") or "gemini-3.6-flash"


def gemini_keys():
    """Paid key first (if you add GEMINI_API_KEY later), then your 5 old keys."""
    names = ["GEMINI_API_KEY"] + [f"GEMINI_KEY_{i}" for i in range(1, 6)]
    keys = []
    for name in names:
        value = (os.environ.get(name) or "").strip()
        if value and value not in keys:
            keys.append(value)
    return keys


# ---------------------------------------------------------------- email / telegram
GMAIL_SENDER = os.environ.get("GMAIL_SENDER") or ""
GMAIL_RECEIVER = os.environ.get("GMAIL_RECEIVER") or GMAIL_SENDER
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") or ""
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or ""

# ---------------------------------------------------------------- images
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY") or ""
# Images found inside news RSS feeds belong to the publishers.
# Leave this False unless you have permission to reuse them.
USE_SOURCE_IMAGES = (os.environ.get("USE_SOURCE_IMAGES") or "").lower() in ("1", "true", "yes")

# ---------------------------------------------------------------- scraping behaviour
USER_AGENT = f"Mozilla/5.0 (compatible; TrendifyBot/1.0; +{SITE_URL})"
ROBOTS_TOKEN = "TrendifyBot"
REQUEST_TIMEOUT = 15
ITEMS_PER_FEED = 5          # how many top entries of each feed to look at
MAX_TRIES_PER_RUN = 8       # max candidates one bot examines per run
SOURCE_TEXT_LIMIT = 6000    # characters of source text passed to the AI

# ---------------------------------------------------------------- files
SEEN_FILE = "data/seen.json"
SEEN_LIMIT = 6000           # remember the last N items
FEEDS_DIR = "data/feeds"
DRAFTS_DIR = "_drafts"      # folders starting with "_" are not published by Jekyll
LOG_FILE = "logs/system.log"
DASHBOARD_FILE = "system-logs.html"
SITEMAP_FILE = "sitemap.xml"
RSS_MAX_ITEMS = 20