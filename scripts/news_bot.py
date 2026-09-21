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
# PATH CORRECTION (Ensures root directory execution)
# ==========================================
# Scripts folder se root directory par switch karta hai taake files ghalat jagah na banein
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)

# ==========================================
# CONFIGURATION & PASSWORDS (GITHUB SECRETS)
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

RSS_FEEDS = [
    # Global Geopolitics, Conflicts & World News Feeds

    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.theguardian.com/world/rss",
    "https://rss.dw.com/rdf/rss-en-world",
    "https://www.france24.com/en/rss",
    "https://moxie.foxnews.com/google-publisher/world.xml",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "http://rss.cnn.com/rss/edition_world.rss",
    "https://www.cbsnews.com/latest/rss/world",
    "https://abcnews.go.com/abcnews/internationalheadlines",
    "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    "https://www.independent.co.uk/news/world/rss",
    "https://www.telegraph.co.uk/world-news/rss.xml",
    "https://www.scmp.com/rss/91/feed",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://dawn.com/feeds/home/",
    "https://tribune.com.pk/feed/latest",
    "https://www.geo.tv/rss/1/53",
    "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    "https://www.japantimes.co.jp/news_category/world/feed/",
    "https://www.straitstimes.com/news/world/rss.xml",
    "https://www.politico.eu/feed/",
    "https://www.euractiv.com/feed/",
    "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
    "https://mercopress.com/rss",
    "https://www.smh.com.au/rss/world.xml",
    "https://theintercept.com/feed/?lang=en",
    "https://defense-update.com/feed",
    "https://www.amnesty.org/en/rss/",
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://mashable.com/feeds/rss/all",
    "https://www.theverge.com/rss/index.xml",
    "http://feeds.arstechnica.com/arstechnica/index",
    "https://www.engadget.com/rss.xml",
    "https://gizmodo.com/rss",
    "https://www.zdnet.com/news/rss.xml",
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://readwrite.com/feed/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.cnet.com/rss/news/",
    "https://www.techradar.com/rss",
    "https://www.technologyreview.com/feed/"
]

# ==========================================
# MODULE: RSS FEED (NEWS ONLY)
# ==========================================
def update_rss(title, file_name, image_url):
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/news/{file_name}"
    post_caption = f"⚡ {title} \n\n👇 Read full details here:\n{website_url}"
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify News - Tech Updates</title>
  <link>https://Muhammad-Mateen-Arshad.github.io/trendify-news/</link>
  <description>Latest Automated Tech News Updates</description>
  <item>
    <title>{title}</title>
    <description>{post_caption}</description>
    <link>{website_url}</link>
    <pubDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
    <enclosure url="{image_url}" type="image/jpeg" length="0" />
  </item>
</channel>
</rss>"""

    with open("rss_news.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("✅ Dedicated RSS Feed Updated: rss_news.xml")

def send_telegram_message(title):
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("⚠️ Telegram Token nahi mila!")
        return
    
    channel_id = "@trendify_news_live"
    website_url = "https://Muhammad-Mateen-Arshad.github.io/trendify-news/"
    message = f"🚨 *LATEST TECH UPDATE* 🚨\n\n⚡ {title}\n\n👇 Read full story:\n{website_url}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("🚀 Telegram par khabar automatically post ho gayi!")
        else:
            print(f"⚠️ Telegram Error: {response.text}")
    except Exception as e:
        print(f"⚠️ Telegram Exception: {e}")

# ==========================================
# MODULE: LOGGER, EMAIL & DASHBOARD ALERTS
# ==========================================
def add_log(status_type, message):
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    log_folder = "logs"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    file_path = os.path.join(log_folder, "system.log")
    log_entry = f"[{current_time}] [NEWS_BOT] [{status_type}] {message}\n"
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

def update_dashboard(status, message):
    current_time = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    
    if status == "SUCCESS":
        log_html = f"""<!-- NEW_LOG_HERE -->
        <div class="log-card">
            <div class="log-left">
                <span class="status-badge">✔ TECH NEWS</span>
                <span class="log-title">{message}</span>
            </div>
            <span class="log-time">🕒 {current_time}</span>
        </div>"""
    else:
        log_html = f"""<!-- NEW_LOG_HERE -->
        <div class="log-card" style="border-left-color: #ff3333;">
            <div class="log-left">
                <span class="status-badge" style="color:#ff3333; border-color:#ff3333; background: rgba(255, 51, 51, 0.1);">❌ NEWS ERROR</span>
                <span class="log-title" style="color: #ff8888;">{message}</span>
            </div>
            <span class="log-time" style="color: #ff3333; border-color: #ff3333;">🕒 {current_time}</span>
        </div>"""
    
    try:
        if os.path.exists("system-logs.html"):
            with open("system-logs.html", "r", encoding="utf-8") as f:
                content = f.read()
            with open("system-logs.html", "w", encoding="utf-8") as f:
                f.write(content.replace("<!-- NEW_LOG_HERE -->", log_html))
    except Exception:
        pass

def send_error_email(error_msg):
    if not GMAIL_APP_PASSWORD:
        add_log("WARNING", "Gmail App Password missing. Email skipped.")
        return

    print("📧 Alert Email bhej raha hoon...")
    try:
        msg = MIMEText(f"Assalam o Alaikum Mateen Bhai,\n\nTrendify News Bot mein error aaya hai:\n\n{error_msg}\n\nCheck karein.")
        msg['Subject'] = '⚠️ Trendify News Alert - Execution Error'
        msg['From'] = GMAIL_SENDER
        msg['To'] = GMAIL_RECEIVER

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, GMAIL_RECEIVER, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"📧 Email Error: {e}")

# ==========================================
# MODULE A: SCRAPER & IMAGE
# ==========================================
def scrape_unposted_news():
    if not os.path.exists("posted_news.txt"):
        open("posted_news.txt", "w", encoding="utf-8").close()
        
    with open("posted_news.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    shuffled_feeds = RSS_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    for feed_url in shuffled_feeds:
        try:
            response = requests.get(feed_url, timeout=15)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_news.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    # Real Image Extract Karne Ka Logic
                    real_image_url = ""
                    if 'media_content' in entry and len(entry.media_content) > 0:
                        real_image_url = entry.media_content[0]['url']
                    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                        real_image_url = entry.media_thumbnail[0]['url']
                    elif 'links' in entry:
                        for link in entry.links:
                            if 'image' in link.get('type', ''):
                                real_image_url = link.href
                                break
                    
                    # Agar original picture na mile toh backup
                    if not real_image_url:
                        encoded_prompt = urllib.parse.quote(entry.title + " global news event realistic photo")
                        real_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": real_image_url
                    }
        except Exception as e:
            print(f"Skipping feed {feed_url} due to error: {e}")
            continue
            
    return None

# ==========================================
# MODULE B: REAL AI CONTENT
# ==========================================
def generate_ai_article(title, raw_text):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("Koi API key nahi mili! GitHub Secrets check karein.")

    prompt = f"""
    You are an expert tech journalist and SEO content writer. Write an engaging, 400-word news article based on this news:
    Title: {title}\nSummary: {raw_text}\n
    Requirements: Format entirely in clean HTML (do NOT output ```html markdown tags, do not include <html> or <body>). Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> and <ul>.
    """
    
    for _ in range(len(GEMINI_API_KEYS)):
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            return response.text.replace("```html", "").replace("```", "").strip()
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"⚠️ Key {CURRENT_KEY_INDEX + 1} limit reached. Switching key...")
                add_log("WARNING", f"Key {CURRENT_KEY_INDEX + 1} hit 429 Limit.")
                CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
                client = genai.Client(api_key=GEMINI_API_KEYS[CURRENT_KEY_INDEX])
                time.sleep(2)
            else:
                raise Exception(f"AI Generation Failed: {error_msg}")
                
    raise Exception("Sari API keys ki limit khatam ho chuki hai! (429)")

# ==========================================
# MODULE C: BUILD ARTICLE HTML
# ==========================================
def build_html_page(title, image_url, ai_content):
    safe_title = "".join(x for x in title if x.isalnum() or x.isspace())
    file_name = safe_title.lower().replace(" ", "-") + ".html"
    current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    news_folder = "news"
    if not os.path.exists(news_folder):
        os.makedirs(news_folder)
        
    file_path = os.path.join(news_folder, file_name)
    
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
    hook_text = clean_text[:130] + "..." if len(clean_text) > 130 else clean_text
    
    new_card_html = f"""<!-- NEW_CARD_HERE -->
        <div class="news-card">
            <img src="{image_url}" alt="News Image">
            <h3>{title}</h3>
            <p>{hook_text}</p>
            <a href="news/{file_name}" class="read-more">Read Full Article</a>
        </div>"""
        
    for page in ["index.html", "articles.html"]:
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
    print("🔥 TECH NEWS BOT RUNNING...\n")
    try:
        news = scrape_unposted_news()
        if news:
            print(f"🤖 AI Article Generating: {news['title']}")
            article = generate_ai_article(news["title"], news["raw_text"])
            file_name = build_html_page(news["title"], news["image_url"], article)
            
            if file_name:
                update_main_pages(news["title"], news["image_url"], file_name, news["raw_text"])
                add_log("SUCCESS", f"Published: {news['title']}")
                update_dashboard("SUCCESS", news["title"])
                update_rss(news["title"], file_name, news["image_url"])
                send_telegram_message(news["title"])
                print("🎉 SUCCESS! Nayi khabar publish aur sync ho chuki hai.")
        else:
            print("⏳ Koi nayi unposted khabar nahi mili.")
    except Exception as e:
        error_details = str(e)
        if "429" in error_details or "RESOURCE_EXHAUSTED" in error_details:
            add_log("WARNING", "All API Keys Exhausted (429).")
        else:
            add_log("ERROR", error_details)
            update_dashboard("ERROR", error_details)
            send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()