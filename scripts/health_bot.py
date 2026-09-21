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

# USA Targeted Health & Senior Care Feeds
# Premium USA Targeted Health & Senior Care Feeds
HEALTH_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    "https://feeds.npr.org/1128/rss.xml",
    "https://medicalxpress.com/rss-feed/health-news/",
    "http://rss.cnn.com/rss/cnn_health.rss",
    "https://moxie.foxnews.com/google-publisher/health.xml",
    "https://www.cbsnews.com/latest/rss/health",
    "https://abcnews.go.com/abcnews/healthheadlines",
    "https://kffhealthnews.org/feed/", 
    "https://www.health.harvard.edu/blog/feed",
    "https://www.statnews.com/feed/",
    "https://news.un.org/feed/subscribe/en/news/topic/health/rss.xml",
    "https://www.medpagetoday.com/rss/headlines.xml"
]

# ==========================================
# MODULE: RSS FEED (HEALTH ONLY)
# ==========================================
def update_rss(title, file_name, image_url):
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/health/{file_name}"
    post_caption = f"🌿 Health Update: {title} \n\n👇 Read the full guide here:\n{website_url}"
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify Portal - Senior Health</title>
  <link>https://Muhammad-Mateen-Arshad.github.io/trendify-news/</link>
  <description>Latest Wellness & Health Tips for Seniors</description>
  <item>
    <title>{title}</title>
    <description>{post_caption}</description>
    <link>{website_url}</link>
    <pubDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
    <enclosure url="{image_url}" type="image/jpeg" length="0" />
  </item>
</channel>
</rss>"""

    with open("rss_health.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("✅ Dedicated RSS Feed Updated: rss_health.xml")

def send_telegram_message(title):
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return
    
    channel_id = "@trendify_news_live"
    website_url = "https://Muhammad-Mateen-Arshad.github.io/trendify-news/health.html"
    message = f"🌿 *NEW HEALTH & WELLNESS GUIDE* 🌿\n\n📌 {title}\n\n👇 Read full article:\n{website_url}"
    
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
            f.write(f"[{current_time}] [HEALTH_BOT] [{status_type}] {message}\n")
    except Exception:
        pass

def send_error_email(error_msg):
    if not GMAIL_APP_PASSWORD:
        return
    try:
        msg = MIMEText(f"Trendify Health Bot Error:\n\n{error_msg}")
        msg['Subject'] = '⚠️ Trendify Health Alert'
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
# ==========================================
# MODULE A: SCRAPER & IMAGE
# ==========================================
def scrape_unposted_health():
    if not os.path.exists("posted_health.txt"):
        open("posted_health.txt", "w", encoding="utf-8").close()
        
    with open("posted_health.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    shuffled_feeds = HEALTH_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    # Browser identity taake websites bot samajh kar block na karein
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    for feed_url in shuffled_feeds:
        try:
            # Strict 15-second timeout and headers added
            response = requests.get(feed_url, headers=headers, timeout=15)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_health.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    # Senior health focused AI image prompt
                    image_prompt = entry.title + " healthy active senior people nature morning sunlight wellness high quality realistic"
                    encoded_prompt = urllib.parse.quote(image_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true&seed={random.randint(1,1000)}"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": image_url
                    }
        except Exception as e:
            print(f"Skipping feed {feed_url} due to error: {e}")
            continue
            
    return None
# ==========================================
# MODULE B: USA 60+ TARGETED AI CONTENT
# ==========================================
def generate_ai_article(title, raw_text):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("API key missing!")

    prompt = f"""
    You are a medical copywriter specializing in senior health. Write a highly engaging, empathetic 400-word wellness article based on this news:
    Topic: {title}\nDetails: {raw_text}\n
    Requirements:
    1. Target Audience: Men and women aged 60 and older living in the United States. Use a respectful, encouraging, and clear tone.
    2. Format entirely in clean HTML (no ```html, no <html> or <body>). 
    3. Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> for headings (like 'Why This Matters for Seniors', 'Simple Steps to Take') and <ul> for lists.
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
    
    health_folder = "health"
    if not os.path.exists(health_folder):
        os.makedirs(health_folder)
        
    file_path = os.path.join(health_folder, file_name)
    
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
            <img src="{image_url}" alt="Health Image">
            <h3>{title}</h3>
            <p>{hook_text}</p>
            <a href="health/{file_name}" class="read-more">Read Full Guide</a>
        </div>"""
        
    page = "health.html"
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
    print("🔥 HEALTH BOT RUNNING...\n")
    try:
        health_news = scrape_unposted_health()
        if health_news:
            print(f"🤖 Generating Senior Health Guide: {health_news['title']}")
            article = generate_ai_article(health_news["title"], health_news["raw_text"])
            file_name = build_html_page(health_news["title"], health_news["image_url"], article)
            
            if file_name:
                update_main_pages(health_news["title"], health_news["image_url"], file_name, health_news["raw_text"])
                add_log("SUCCESS", f"Health Post Published: {health_news['title']}")
                update_rss(health_news["title"], file_name, health_news["image_url"])
                send_telegram_message(health_news["title"])
                print("🎉 SUCCESS! Nayi Health post ho chuki hai.")
        else:
            print("⏳ Koi nayi health news nahi mili.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()
