"""Small text helpers."""
import html
import re

_TAG = re.compile(r"<[^>]+>")
_SCRIPTS = re.compile(r"(?is)<(script|style)\b.*?</\1>")


def html_to_text(value):
    """Turn HTML (or plain text) into clean, single-spaced plain text."""
    value = _SCRIPTS.sub(" ", value or "")
    value = _TAG.sub(" ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def esc(value):
    """HTML-escape text that goes inside a page or an attribute."""
    return html.escape(value or "", quote=True)


def shorten(value, limit):
    value = value or ""
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."