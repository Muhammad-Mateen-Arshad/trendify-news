"""The one pipeline used by all six bots.

feeds -> skip seen -> real link + source text -> AI (source only)
      -> quality gate -> image -> publish -> card / RSS / sitemap -> dashboard + Telegram

One bot run publishes at most ONE article (same as before). If an item is
too thin or fails the quality gate, the bot simply tries the next item.
"""
from collections import Counter
from pathlib import Path

from . import ai as ai_module
from . import config, images, notify, publish, quality, sources
from .ai import AIClient, AIUnavailable
from .dedupe import SeenStore
from .niches import NICHES


def _safe(niche, what, fn, *args):
    """Run a non-critical step. A failure is logged but never stops the bot."""
    try:
        return fn(*args)
    except Exception as e:
        notify.log(niche.label, "WARN", f"{what} failed: {type(e).__name__}: {e}")
        return None


def _save_draft(niche, title, link, body_html, reasons):
    folder = Path(config.DRAFTS_DIR) / niche.name
    folder.mkdir(parents=True, exist_ok=True)
    header = "<!-- REJECTED: " + "; ".join(reasons).replace("--", "-") + "\nSOURCE: " + link + " -->\n"
    (folder / publish.make_filename(title, link)).write_text(header + body_html, encoding="utf-8")


def _process(niche, candidate, ai, seen):
    """Handle one feed item. Returns: published / thin / rejected."""
    source = sources.gather(candidate)

    if len(source.text) < niche.min_source_chars:
        notify.log(niche.label, "INFO", f"Skipped (source text too thin, {len(source.text)} chars): {candidate.title[:70]}")
        seen.mark(candidate.title, candidate.link, "thin", niche.name)
        return "thin"

    body = ai.write_article(niche, candidate.title, source.publisher, source.text)

    ok, reasons = quality.check(niche, body, source.text, candidate.title)
    if not ok:
        _save_draft(niche, candidate.title, source.link, body, reasons)
        notify.log(niche.label, "INFO", f"Rejected by quality gate ({'; '.join(reasons)}): {candidate.title[:70]}")
        seen.mark(candidate.title, candidate.link, "rejected", niche.name)
        return "rejected"

    image_url, credit = images.pick(niche, candidate)
    filename, url = publish.build_article(niche, candidate.title, body, image_url, credit, source)

    # The article file exists now: remember it BEFORE the optional steps,
    # so a later failure can never cause the same article to be posted twice.
    seen.mark(candidate.title, candidate.link, "posted", niche.name)

    _safe(niche, "Category card", publish.add_card, niche, candidate.title, image_url, filename, body)
    _safe(niche, "RSS update", publish.update_rss, niche, candidate.title, url, image_url)
    _safe(niche, "Sitemap update", publish.update_sitemap)
    notify.log(niche.label, "SUCCESS", f"Published: {candidate.title}")
    notify.dashboard(niche, "SUCCESS", f"Published: {candidate.title}")
    notify.telegram(niche, candidate.title, url)
    return "published"


def _fail(niche, message):
    notify.log(niche.label, "ERROR", message)
    notify.dashboard(niche, "ERROR", message[:200])
    notify.send_error_email(niche.label, message)


def run_niche(name):
    """Run one bot. Returns 0 on success (even if nothing new was found), 1 on error."""
    niche = NICHES[name]
    print(f"🔥 {niche.label} BOT RUNNING...\n")

    seen = SeenStore()
    seen.import_legacy(niche)
    ai = AIClient()
    stats = Counter()
    last_error = ""

    try:
        for candidate in sources.iter_candidates(niche):
            if seen.is_seen(candidate.title, candidate.link):
                stats["already_seen"] += 1
                continue
            if stats["tried"] >= config.MAX_TRIES_PER_RUN:
                break
            stats["tried"] += 1
            try:
                outcome = _process(niche, candidate, ai, seen)
            except AIUnavailable:
                raise
            except Exception as e:
                outcome = "error"
                last_error = f"{type(e).__name__}: {e}"
                notify.log(niche.label, "ERROR", f"{candidate.title[:70]} -> {last_error}")
            stats[outcome] += 1
            if outcome == "published":
                break
    except AIUnavailable as e:
        _fail(niche, f"AI unavailable: {e}")
        return 1

    u = ai_module.usage
    if u["calls"]:
        notify.log(niche.label, "INFO", f"AI usage: {u['calls']} calls, {u['prompt_tokens']} in / {u['output_tokens']} out tokens")

    if stats["published"]:
        return 0
    if stats["error"]:
        _fail(niche, f"Nothing published. Last error: {last_error}")
        return 1
    notify.log(niche.label, "INFO", f"Nothing published this run: {dict(stats)}")
    return 0