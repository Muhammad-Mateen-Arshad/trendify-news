import time
import os
import requests
import feedparser
import random
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import re  
from google import genai
import tweepy

# ==========================================
# CONFIGURATION & PASSWORDS (GITHUB SECRETS)
# ==========================================
# 🌟 Tijori se keys nikalne ka Jadu
GEMINI_API_KEYS = [
    os.environ.get("GEMINI_KEY_1"),
    os.environ.get("GEMINI_KEY_2"), 
    os.environ.get("GEMINI_KEY_3"),
    os.environ.get("GEMINI_KEY_4"),
    os.environ.get("GEMINI_KEY_5")
]

# Agar koi key khali ho toh usay ignore kar dega
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

CURRENT_KEY_INDEX = 0

# Failsafe: System secure initialize karne ke liye
if GEMINI_API_KEYS:
    client = genai.Client(api_key=GEMINI_API_KEYS[CURRENT_KEY_INDEX])
else:
    client = None

MODEL_NAME = 'gemini-3.6-flash' 

GMAIL_SENDER = "mateenarshad877@gmail.com" 
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") 
GMAIL_RECEIVER = "mateenarshad877@gmail.com" 

RSS_FEEDS = [
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

def send_telegram_message(title):
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("⚠️ Telegram Token nahi mila!")
        return
    
    channel_id = "@trendify_news_live"
    website_url = "https://Muhammad-Mateen-Arshad.github.io/trendify-news/"
    
    # Catchy Message for Telegram
    message = f"🚨 *LATEST NEWS UPDATE* 🚨\n\n⚡ {title}\n\n👇 Read the full story now:\n{website_url}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("🚀 Telegram par khabar automatically post ho gayi!")
        else:
            print(f"⚠️ Telegram Error: {response.text}")
    except Exception as e:
        print(f"⚠️ Telegram Exception: {e}")

import os
import requests 

def send_to_make_webhook(title, file_name):
    # --- 🛑 Anti-Error Filter (503 / API Errors rokne ke liye) ---
    forbidden_words = ["503", "error", "failed", "unavailable", "bad gateway"]
    # Check karein agar title mein koi error word majood hai
    if any(word in title.lower() for word in forbidden_words):
        print(f"🛑 Kharab title rok liya gaya (Error detected): {title}")
        return

    # --- 🛡️ Duplicate Check (Bot ki Yaadasht) ---
    history_file = "posted_history.txt"
    
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            if file_name in f.read():
                print(f"⏩ Yeh khabar Twitter par pehle hi ja chuki hai (Skipping): {title}")
                return

    # 👇 Yahan in commas ke andar apna Make.com ka Webhook link paste karein
    webhook_url = "https://hook.us2.make.com/oh9njxe3rrwa9mg9sx462q9pphnwca82"
    
    # Direct article ka link
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/news/{file_name}"
    
    # Tweet ka Text
    tweet_text = f"🚨 LATEST TECH NEWS 🚨\n\n⚡ {title}\n\n👇 Read full story here:\n{website_url}\n\n#TechNews #AI #Trendify"

    payload = {
        "text": tweet_text
    }

    try:
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 200 or response.status_code == 201 or response.text.lower() == "accepted":
            print("✅ Make.com Webhook par data kamyabi se chala gaya!")
            
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(file_name + "\n")
                
        else:
            print(f"⚠️ Webhook Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Python Webhook Error: {e}")

# ==========================================
# MODULE: LOGGER, EMAIL & DASHBOARD ALERTS
# ==========================================
def add_log(status_type, message):
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    log_folder = "logs"
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    file_path = os.path.join(log_folder, "system.log")
    log_entry = f"[{current_time}] [{status_type}] {message}\n"
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
                <span class="status-badge">✔ PUBLISHED</span>
                <span class="log-title">{message}</span>
            </div>
            <span class="log-time">🕒 {current_time}</span>
        </div>"""
    else:
        log_html = f"""<!-- NEW_LOG_HERE -->
        <div class="log-card" style="border-left-color: #ff3333;">
            <div class="log-left">
                <span class="status-badge" style="color:#ff3333; border-color:#ff3333; background: rgba(255, 51, 51, 0.1);">❌ ERROR</span>
                <span class="log-title" style="color: #ff8888;">{message}</span>
            </div>
            <span class="log-time" style="color: #ff3333; border-color: #ff3333;">🕒 {current_time}</span>
        </div>"""
    
    try:
        with open("system-logs.html", "r", encoding="utf-8") as f:
            content = f.read()
        with open("system-logs.html", "w", encoding="utf-8") as f:
            f.write(content.replace("<!-- NEW_LOG_HERE -->", log_html))
    except Exception as e:
        pass

def send_error_email(error_msg):
    if not GMAIL_APP_PASSWORD:
        add_log("WARNING", "Gmail App Password missing. Email skipped.")
        return

    print("📧 Alert Email bhej raha hoon...")
    try:
        msg = MIMEText(f"Assalam o Alaikum Mateen Bhai,\n\nTrendify bot mein ek error aaya hai. Details yeh hain:\n\n{error_msg}\n\nJaldi check karein!")
        msg['Subject'] = '⚠️ Trendify Bot Alert - System Error'
        msg['From'] = GMAIL_SENDER
        msg['To'] = GMAIL_RECEIVER

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, GMAIL_RECEIVER, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"📧 Email Error: {e}")

# ==========================================
# MODULE A: SCRAPER & AI IMAGE GENERATOR
# ==========================================
def scrape_unposted_news():
    if not os.path.exists("posted.txt"):
        open("posted.txt", "w").close()
        
    with open("posted.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    random.shuffle(RSS_FEEDS) 
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    image_prompt = entry.title + " technology futuristic high quality realistic"
                    encoded_prompt = urllib.parse.quote(image_prompt)
                    ai_generated_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true"
                    
                    return {
                        "title": entry.title,
                        "raw_text": entry.summary,
                        "image_url": ai_generated_image_url
                    }
        except Exception as e:
            continue
    return None

# ==========================================
# MODULE B: REAL AI CONTENT (5-KEY AUTO-ROTATOR)
# ==========================================
def generate_ai_article(title, raw_text):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("Koi API key nahi mili! GitHub Secrets check karein.")

    prompt = f"""
    You are an expert tech journalist and SEO content writer. Write a highly engaging, 400-word news article based on this news:
    Title: {title}\nSummary: {raw_text}\n
    Requirements: Format entirely in HTML (no ```html tags, no <html> or <body> tags). Use <p>, <h3 style="color: #FFD700; margin-top: 30px;"> and <ul>.
    """
    
    for _ in range(len(GEMINI_API_KEYS)):
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            return response.text.replace("```html", "").replace("```", "")
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"⚠️ Key {CURRENT_KEY_INDEX + 1} ki limit khatam. Dusri key par shift kar raha hoon...")
                add_log("WARNING", f"Key {CURRENT_KEY_INDEX + 1} hit 429 Limit. Switching key...")
                
                CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
                client = genai.Client(api_key=GEMINI_API_KEYS[CURRENT_KEY_INDEX])
                time.sleep(2) 
            else:
                raise Exception(f"AI Generation Failed: {error_msg}")
                
    raise Exception("Sari API keys ki limit khatam ho chuki hai! (429)")

# ==========================================
# MODULE C: CLEAN TEMPLATE BUILDER 
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
# MODULE D: POSTER 
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
        try:
            with open(page, "r", encoding="utf-8") as f:
                content = f.read()
            with open(page, "w", encoding="utf-8") as f:
                f.write(content.replace("<!-- NEW_CARD_HERE -->", new_card_html))
        except:
            pass

# ==========================================
# 🚀 SINGLE RUN PIPELINE (For Cloud Automation)
# ==========================================
def run_single_pipeline():
    print("🔥 GITHUB ACTION TRIGGERED! Checking for news...\n")
    try:
        news = scrape_unposted_news()
        if news:
            print(f"🤖 AI Article likh raha hai: {news['title']}")
            article = generate_ai_article(news["title"], news["raw_text"])
            file_name = build_html_page(news["title"], news["image_url"], article)
            
            if file_name:
                update_main_pages(news["title"], news["image_url"], file_name, news["raw_text"])
                add_log("SUCCESS", f"Published: {news['title']}")
                update_dashboard("SUCCESS", news["title"])
                print("🎉 SUCCESS! Nayi khabar post ho gayi.")
               # Telegram par bhejne ke liye
                send_telegram_message(news["title"])
             # Make.com (Buffer) par bhejne ke liye
                send_to_make_webhook(news["title"], file_name)
        else:
            print("⏳ Koi nayi khabar nahi mili.")
    except Exception as e:
        error_details = str(e)
        if "429" in error_details or "RESOURCE_EXHAUSTED" in error_details:
            add_log("WARNING", "All 5 API Keys Exhausted.")
        else:
            add_log("ERROR", error_details)
            update_dashboard("ERROR", error_details)
            send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()

   

