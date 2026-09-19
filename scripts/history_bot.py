import time
from datetime import datetime
import os
import requests
import feedparser
import random
import urllib.parse
import smtplib
from email.mime.text import MIMEText
import re  
from google import genai

# ==========================================
# PATH CORRECTION
# ==========================================
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)

# ==========================================
# CONFIGURATION
# ==========================================
GEMINI_API_KEYS = [
    os.environ.get("GEMINI_KEY_1"),
    os.environ.get("GEMINI_KEY_2"), 
    os.environ.get("GEMINI_KEY_3"),
    os.environ.get("GEMINI_KEY_4"),
    os.environ.get("GEMINI_KEY_5")
]

GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]
CURRENT_KEY_INDEX = 0

if GEMINI_API_KEYS:
    client = genai.Client(api_key=GEMINI_API_KEYS[CURRENT_KEY_INDEX])
else:
    client = None

MODEL_NAME = 'gemini-3.6-flash'
GMAIL_SENDER = "mateenarshad877@gmail.com" 
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") 
GMAIL_RECEIVER = "mateenarshad877@gmail.com" 

# History, Archaeology & Science Documentaries Feeds
HISTORY_FEEDS = [
    "https://www.smithsonianmag.com/rss/history/",
    "https://www.livescience.com/feeds/all",
    "https://phys.org/rss-feed/science-news/history/",
    "https://www.archaeology.org/news?format=feed"
]

# ==========================================
# MODULE: RSS FEED (HISTORY ONLY)
# ==========================================
def update_rss(title, file_name, image_url):
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/history/{file_name}"
    post_caption = f"🦕 Historical Doc: {title} \n\n👇 Dive into history here:\n{website_url}"
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify Portal - History & Docs</title>
  <link>https://Muhammad-Mateen-Arshad.github.io/trendify-news/</link>
  <description>Epic Historical Biographies & Prehistoric Wildlife Documentaries</description>
  <item>
    <title>{title}</title>
    <description>{post_caption}</description>
    <link>{website_url}</link>
    <pubDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
    <enclosure url="{image_url}" type="image/jpeg" length="0" />
  </item>
</channel>
</rss>"""

    with open("rss_history.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("✅ Dedicated RSS Feed Updated: rss_history.xml")

def send_telegram_message(title):
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return
    
    channel_id = "@trendify_news_live"
    website_url = "https://Muhammad-Mateen-Arshad.github.io/trendify-news/history.html"
    message = f"🦕 *EPIC HISTORY & DOCS* 🎬\n\n📌 {title}\n\n👇 Read the full story:\n{website_url}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": channel_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

# ==========================================
# MODULE: LOGGER
# ==========================================
def add_log(status_type, message):
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    log_folder = "logs"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    file_path = os.path.join(log_folder, "system.log")
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[{current_time}] [HISTORY_BOT] [{status_type}] {message}\n")
    except Exception:
        pass

def send_error_email(error_msg):
    if not GMAIL_APP_PASSWORD:
        return
    try:
        msg = MIMEText(f"Trendify History Bot Error:\n\n{error_msg}")
        msg['Subject'] = '⚠️ Trendify History Alert'
        msg['From'] = GMAIL_SENDER
        msg['To'] = GMAIL_RECEIVER
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, GMAIL_RECEIVER, msg.as_string())
        server.quit()
    except Exception:
        pass

# ==========================================
# MODULE A: SCRAPER & IMAGE
# ==========================================
def scrape_unposted_history():
    if not os.path.exists("posted_history.txt"):
        open("posted_history.txt", "w", encoding="utf-8").close()
        
    with open("posted_history.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    shuffled_feeds = HISTORY_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    for feed_url in shuffled_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_history.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    # Cinematic & Documentary vibe lock
                    image_prompt = entry.title + " epic cinematic wildlife documentary historical dramatic lighting high quality"
                    encoded_prompt = urllib.parse.quote(image_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true&seed={random.randint(1,1000)}"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": image_url
                    }
        except Exception:
            continue
    return None

# ==========================================
# MODULE B: DOCUMENTARY STYLE AI CONTENT
# ==========================================
def generate_ai_article(title, raw_text):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("API key missing!")

    prompt = f"""
    You are an expert documentary scriptwriter and historian. Write a highly captivating, 400-word article based on this finding/news:
    Topic: {title}\nDetails: {raw_text}\n
    Requirements:
    1. Tone: Epic, immersive, and narrative-driven (similar to a premium historical or prehistoric wildlife documentary).
    2. Format entirely in clean HTML (no ```html, no <html> or <body>). 
    3. Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> for dramatic section headers (e.g., 'The Discovery', 'Echoes of the Past') and <ul> for fascinating facts.
    """
    
    for _ in range(len(GEMINI_API_KEYS)):
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            return response.text.replace("```html", "").replace("```", "").strip()
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
                client = genai.Client(api_key=GEMINI_API_KEYS[CURRENT_KEY_INDEX])
                time.sleep(2)
            else:
                raise Exception(f"AI Generation Failed: {error_msg}")
                
    raise Exception("All API keys exhausted! (429)")

# ==========================================
# MODULE C: BUILD ARTICLE HTML
# ==========================================
def build_html_page(title, image_url, ai_content):
    safe_title = "".join(x for x in title if x.isalnum() or x.isspace())
    file_name = safe_title.lower().replace(" ", "-") + ".html"
    current_time = datetime.now().strftime("%B %d, %Y")
    
    history_folder = "history"
    if not os.path.exists(history_folder):
        os.makedirs(history_folder)
        
    file_path = os.path.join(history_folder, file_name)
    
    with open("article_template.html", "r", encoding="utf-8") as f:
        html_template = f.read()
        
    final_html = html_template.replace("{{TITLE}}", title).replace("{{IMAGE_URL}}", image_url).replace("{{CURRENT_TIME}}", current_time).replace("{{AI_CONTENT}}", ai_content)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(final_html)
        
    return file_name

# ==========================================
# MODULE D: UPDATE FRONTEND PAGES
# ==========================================
def update_main_pages(title, image_url, file_name, raw_text):
    clean_text = re.sub(r'<[^>]+>', '', raw_text).strip()
    hook_text = clean_text[:120] + "..." if len(clean_text) > 120 else clean_text
    
    new_card_html = f"""<!-- NEW_CARD_HERE -->
        <div class="news-card">
            <img src="{image_url}" alt="History Image">
            <h3>{title}</h3>
            <p>{hook_text}</p>
            <a href="history/{file_name}" class="read-more">Read Full Story</a>
        </div>"""
        
    page = "history.html"
    if os.path.exists(page):
        try:
            with open(page, "r", encoding="utf-8") as f:
                content = f.read()
            with open(page, "w", encoding="utf-8") as f:
                f.write(content.replace("<!-- NEW_CARD_HERE -->", new_card_html))
        except Exception:
            pass

# ==========================================
# 🚀 PIPELINE RUNNER
# ==========================================
def run_single_pipeline():
    print("🔥 HISTORY BOT RUNNING...\n")
    try:
        doc_news = scrape_unposted_history()
        if doc_news:
            print(f"🤖 Generating Documentary Article: {doc_news['title']}")
            article = generate_ai_article(doc_news["title"], doc_news["raw_text"])
            file_name = build_html_page(doc_news["title"], doc_news["image_url"], article)
            
            if file_name:
                update_main_pages(doc_news["title"], doc_news["image_url"], file_name, doc_news["raw_text"])
                add_log("SUCCESS", f"History Post Published: {doc_news['title']}")
                update_rss(doc_news["title"], file_name, doc_news["image_url"])
                send_telegram_message(doc_news["title"])
                print("🎉 SUCCESS! Nayi History post ho chuki hai.")
        else:
            print("⏳ Koi nayi history doc nahi mili.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()