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

# ==========================================
# 50 HISTORY, ARCHAEOLOGY & ANCIENT WORLD FEEDS
# ==========================================
HISTORY_FEEDS = [
    # General History & Archaeology
    "https://news.google.com/rss/search?q=archaeology+discoveries&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=historical+discoveries&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=world+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=ancient+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=history+museum+exhibits&hl=en-US&gl=US&ceid=US:en",
    
    # Civilizations & Empires
    "https://news.google.com/rss/search?q=ancient+egypt+archaeology&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=roman+empire+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=ancient+greece+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=ottoman+empire+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=byzantine+empire+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=mayan+civilization+discoveries&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=aztec+empire+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=inca+empire+archaeology&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=mesopotamia+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=indus+valley+civilization&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=viking+history+discoveries&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=mongol+empire+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=persian+empire+history&hl=en-US&gl=US&ceid=US:en",
    
    # Regions
    "https://news.google.com/rss/search?q=european+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=asian+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=african+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=middle+east+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=american+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=native+american+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=islamic+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=subcontinent+history+india+pakistan&hl=en-US&gl=US&ceid=US:en",
    
    # Specific Eras
    "https://news.google.com/rss/search?q=stone+age+discoveries&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=bronze+age+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=iron+age+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=middle+ages+medieval+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=renaissance+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=victorian+era+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=world+war+1+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=world+war+2+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=cold+war+history&hl=en-US&gl=US&ceid=US:en",
    
    # Niche History
    "https://news.google.com/rss/search?q=history+of+science&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=history+of+medicine&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=history+of+art&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=military+history+battles&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=maritime+history+shipwrecks&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=paleontology+dinosaur+discoveries&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=fossil+discoveries&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=royal+family+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=mythology+and+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=ancient+languages+deciphered&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=historical+artifacts+found&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=historical+documents+uncovered&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=history+of+technology&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=space+exploration+history&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=historical+biographies&hl=en-US&gl=US&ceid=US:en"
]

# ==========================================
# MODULE: RSS FEED (HISTORY ONLY)
# ==========================================
def update_rss(title, file_name, image_url):
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/history/{file_name}"
    post_caption = f"📜 Historical Fact: {title} \n\n👇 Read the full story here:\n{website_url}"
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify Portal - History & Archaeology</title>
  <link>https://Muhammad-Mateen-Arshad.github.io/trendify-news/</link>
  <description>Latest Historical Discoveries and World History Stories</description>
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
    message = f"📜 *NEW HISTORICAL DISCOVERY* 🏛️\n\n📌 {title}\n\n👇 Read full story:\n{website_url}"
    
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

def update_dashboard(status, message):
    current_time = datetime.now().strftime("%b %d, %Y - %I:%M %p")
    bot_name = "HISTORY" # ⚠️ Har bot mein isay change karein (e.g., "HEALTH", "HISTORY", "DRAMAS")
    
    if status == "SUCCESS":
        log_html = f"""<!-- NEW_LOG_HERE -->
        <tr>
            <td><strong>{bot_name}</strong></td>
            <td><span class="status-badge posted">POSTED</span></td>
            <td class="time-text">{current_time}</td>
            <td style="color: #94a3b8;">{message}</td>
        </tr>"""
    else:
        log_html = f"""<!-- NEW_LOG_HERE -->
        <tr style="background-color: rgba(255, 51, 51, 0.05);">
            <td><strong>{bot_name}</strong></td>
            <td><span class="status-badge error">ERROR</span></td>
            <td class="time-text">{current_time}</td>
            <td style="color: #ff8888;">{message}</td>
        </tr>"""
    
    try:
        if os.path.exists("system-logs.html"):
            with open("system-logs.html", "r", encoding="utf-8") as f:
                content = f.read()
            with open("system-logs.html", "w", encoding="utf-8") as f:
                f.write(content.replace("<!-- NEW_LOG_HERE -->", log_html))
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
    
    # Anti-bot block bypass headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    for feed_url in shuffled_feeds:
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            # 🔥 503 aur Website Down Error Bypass 🔥
            if response.status_code in [503, 500, 502, 403]:
                continue
                
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_history.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    # 🔥 Real Image Logic 🔥
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
                    
                    # AI Backup
                    if not real_image_url:
                        image_prompt = entry.title + " ancient history historical artifact cinematic epic scene high quality realistic"
                        encoded_prompt = urllib.parse.quote(image_prompt)
                        real_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true&seed={random.randint(1,1000)}"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": real_image_url,
                        "source_link": getattr(entry, 'link', 'https://www.google.com/search?q=historical+discoveries') 
                    }
        except Exception:
            continue
            
    return None

# ==========================================
# MODULE B: HISTORIAN AI CONTENT
# ==========================================
def generate_ai_article(title, raw_text, source_link):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("API key missing!")

    prompt = f"""
    You are an expert historian and archaeologist. Write a fascinating 300-400 word historical account based on this news:
    Topic: {title}\nDetails: {raw_text}\n
    Requirements:
    1. Tone: Educational, mysterious, and highly engaging.
    2. Format entirely in clean HTML (no ```html, no <html> or <body>). 
    3. Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> for headings (e.g., 'Historical Context', 'Why This Matters') and <ul> for key facts.
    4. At the exact end of the article, add this exact HTML button block for the original source:
    
    <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
        <a href="{source_link}" target="_blank" style="background-color: #8B4513; color: #fff; padding: 15px 30px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: 0.3s; text-transform: uppercase;">
            📖 Read Full Historical Account
        </a>
    </div>
    """
    
    for _ in range(len(GEMINI_API_KEYS)):
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            return response.text.replace("```html", "").replace("```", "").strip()
        except Exception as e:
            error_msg = str(e)
            
            # 1. Agar API limit khatam ho (429) toh next key par shift karein
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
                client = genai.Client(api_key=GEMINI_API_KEYS[CURRENT_KEY_INDEX])
                print(f"Key rotated! Switching to Key {CURRENT_KEY_INDEX + 1}")
                time.sleep(2)
                
            # 2. Agar Server overload (503) ho toh 5 second wait kar ke dobara try karein
            elif "503" in error_msg or "500" in error_msg or "502" in error_msg:
                print("⚠️ 503 Server Error. API is overloaded. Waiting 5 seconds before retrying...")
                time.sleep(5)
                
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
            <a href="history/{file_name}" class="read-more">Uncover History</a>
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
        history_news = scrape_unposted_history()
        if history_news:
            print(f"🤖 Generating History Article: {history_news['title']}")
            
            article = generate_ai_article(history_news["title"], history_news["raw_text"], history_news["source_link"])
            file_name = build_html_page(history_news["title"], history_news["image_url"], article)
            
            if file_name:
                update_main_pages(history_news["title"], history_news["image_url"], file_name, history_news["raw_text"])
                add_log("SUCCESS", f"History Post Published: {history_news['title']}")
                update_rss(history_news["title"], file_name, history_news["image_url"])
                send_telegram_message(history_news["title"])
                print("🎉 SUCCESS! Nayi History post ho chuki hai.")
        else:
            print("⏳ Koi nayi history update nahi mili.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        send_error_email(error_details)

# ==========================================
# 🚀 PIPELINE RUNNER (HISTORY)
# ==========================================
def run_single_pipeline():
    print("🔥 HISTORY BOT RUNNING...\n")
    try:
        history_news = scrape_unposted_history()
        if history_news:
            print(f"🤖 Generating History Article: {history_news['title']}")
            article = generate_ai_article(history_news["title"], history_news["raw_text"])
            file_name = build_html_page(history_news["title"], history_news["image_url"], article)
            
            if file_name:
                update_main_pages(history_news["title"], history_news["image_url"], file_name, history_news["raw_text"])
                add_log("SUCCESS", f"History Post Published: {history_news['title']}")
                update_dashboard("SUCCESS", f"Published: {history_news['title']}")
                update_rss(history_news["title"], file_name, history_news["image_url"])
                send_telegram_message(history_news["title"])
                print("🎉 SUCCESS! Nayi History post ho chuki hai.")
        else:
            print("⏳ Koi nayi history news nahi mili.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        update_dashboard("ERROR", error_details)
        send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()