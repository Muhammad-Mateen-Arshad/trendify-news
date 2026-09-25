"""Logging, Telegram, error emails and the system-logs.html dashboard.

Nothing in here is allowed to crash a bot: every function catches its own
errors and writes them to the log instead of hiding them.
"""
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

import requests

from . import config
from .textutil import esc

DASHBOARD_MARKER = "<!-- NEW_LOG_HERE -->"


def log(label, level, message):
    """Append one line to logs/system.log and print it."""
    stamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    line = f"[{stamp}] [{label}_BOT] [{level}] {message}"
    print(line)
    try:
        path = Path(config.LOG_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:  # logging must never crash the bot
        print(f"(could not write log file: {e})")


def telegram(niche, title, article_url):
    if not config.TELEGRAM_TOKEN:
        return
    text = (
        f"{niche.emoji} <b>{esc(niche.telegram_heading)}</b>\n\n"
        f"📌 {esc(title)}\n\n"
        f'👇 <a href="{esc(article_url)}">Read full details</a>'
    )
    payload = {
        "chat_id": config.TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage",
            json=payload, timeout=15,
        )
        if resp.status_code != 200:
            log(niche.label, "WARN", f"Telegram returned {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        log(niche.label, "WARN", f"Telegram failed: {e}")


def send_error_email(niche_label, error_message):
    if not (config.GMAIL_APP_PASSWORD and config.GMAIL_SENDER):
        log(niche_label, "WARN", "Email alert skipped (GMAIL_SENDER / GMAIL_APP_PASSWORD not set)")
        return
    try:
        msg = MIMEText(f"Trendify {niche_label} bot error:\n\n{error_message}")
        msg["Subject"] = f"Trendify {niche_label} - execution error"
        msg["From"] = config.GMAIL_SENDER
        msg["To"] = config.GMAIL_RECEIVER
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(config.GMAIL_SENDER, config.GMAIL_APP_PASSWORD)
            server.sendmail(config.GMAIL_SENDER, [config.GMAIL_RECEIVER], msg.as_string())
    except Exception as e:
        log(niche_label, "WARN", f"Email alert failed: {e}")


def dashboard(niche, status, message):
    """Add a row to system-logs.html. status is 'SUCCESS' or 'ERROR'."""
    stamp = datetime.now().strftime("%b %d, %I:%M %p")
    name = esc(niche.label)
    msg = esc(message)
    if status == "SUCCESS":
        row = (
            f"{DASHBOARD_MARKER}\n"
            f"        <tr>\n"
            f"            <td><strong>{name}</strong></td>\n"
            f'            <td><span class="status-badge posted">POSTED</span></td>\n'
            f'            <td class="time-text">{stamp}</td>\n'
            f'            <td style="color: #94a3b8;">{msg}</td>\n'
            f"        </tr>"
        )
    else:
        row = (
            f"{DASHBOARD_MARKER}\n"
            f'        <tr style="background-color: rgba(255, 51, 51, 0.05);">\n'
            f"            <td><strong>{name}</strong></td>\n"
            f'            <td><span class="status-badge error">ERROR</span></td>\n'
            f'            <td class="time-text">{stamp}</td>\n'
            f'            <td style="color: #ff8888;">{msg}</td>\n'
            f"        </tr>"
        )
    try:
        path = Path(config.DASHBOARD_FILE)
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8")
        if DASHBOARD_MARKER not in content:
            log(niche.label, "WARN", f"{DASHBOARD_MARKER} not found in {config.DASHBOARD_FILE}")
            return
        path.write_text(content.replace(DASHBOARD_MARKER, row, 1), encoding="utf-8")
    except Exception as e:
        log(niche.label, "WARN", f"Dashboard update failed: {e}")