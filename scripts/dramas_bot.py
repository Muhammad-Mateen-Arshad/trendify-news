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

# Entertainment & Drama Feeds (Mix of general TV and historical drama sources)
# ==========================================
# 50 ENTERTAINMENT & DRAMA FEEDS
# ==========================================
# ==========================================
# TARGETED ENTERTAINMENT & TRAILERS FEEDS
# ==========================================
DRAMA_FEEDS = [
    # Turkish Historical (Top Priority)
    "https://news.google.com/rss/search?q=Mehmed+Fetihler+Sultani+trailer+OR+episode+when:2d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Kurulus+Osman+fragman+OR+trailer+when:2d&hl=en-US&gl=US&ceid=US:en",
    
    # Global Netflix / Web Series
    "https://news.google.com/rss/search?q=Netflix+new+series+trailer+release+when:1d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Money+Heist+spinoff+trailer+when:7d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Amazon+Prime+series+trailer+when:1d&hl=en-US&gl=US&ceid=US:en",
    
    # Bollywood & Indian Cinema
    "https://news.google.com/rss/search?q=Bollywood+movie+trailer+release+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=Indian+web+series+trailer+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    
    # Hollywood & General Entertainment
    "https://news.google.com/rss/search?q=Hollywood+movie+trailer+official+when:1d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=HBO+Max+series+trailer+when:1d&hl=en-US&gl=US&ceid=US:en"
]

# ==========================================
# MODULE A: SCRAPER & IMAGE (Dramas)
# ==========================================
def scrape_unposted_dramas():
    if not os.path.exists("posted_dramas.txt"):
        open("posted_dramas.txt", "w", encoding="utf-8").close()
        
    with open("posted_dramas.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    # Sequential Check: Priority wise feeds check hongi
    for feed_url in DRAMA_FEEDS:
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            if response.status_code in [503, 500, 502, 403]:
                continue
                
            feed = feedparser.parse(response.content)
            
            # Sirf top 3 results check karega
            for entry in feed.entries[:3]:
                if entry.title not in posted_history:
                    with open("posted_dramas.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    real_image_url = ""
                    if 'media_content' in entry and len(entry.media_content) > 0:
                        real_image_url = entry.media_content[0]['url']
                    elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                        real_image_url = entry.media_thumbnail[0]['url']
                    
                    if not real_image_url:
                        encoded_prompt = urllib.parse.quote(entry.title + " cinematic high quality tv series movie trailer shot")
                        real_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true"
                    
                    # Original link pass ho raha hai taake article end mein Official button lag sakay
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": real_image_url,
                        "original_link": getattr(entry, 'link', 'https://www.youtube.com')
                    }
        except Exception:
            continue
    return None


# ==========================================
# MODULE: RSS FEED (DRAMAS ONLY)
# ==========================================
def update_rss(title, file_name, image_url):
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/dramas/{file_name}"
    post_caption = f"⚔️ Drama Update: {title} \n\n👇 Read the full breakdown here:\n{website_url}"
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify Portal - Dramas</title>
  <link>https://Muhammad-Mateen-Arshad.github.io/trendify-news/</link>
  <description>Latest Historical and Turkish Drama Updates</description>
  <item>
    <title>{title}</title>
    <description>{post_caption}</description>
    <link>{website_url}</link>
    <pubDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
    <enclosure url="{image_url}" type="image/jpeg" length="0" />
  </item>
</channel>
</rss>"""

    with open("rss_dramas.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("✅ Dedicated RSS Feed Updated: rss_dramas.xml")

def send_telegram_message(title):
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return
    
    channel_id = "@trendify_news_live"
    website_url = "https://Muhammad-Mateen-Arshad.github.io/trendify-news/dramas.html"
    message = f"⚔️ *NEW DRAMA UPDATE* 🎬\n\n📌 {title}\n\n👇 Check the full details:\n{website_url}"
    
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
            f.write(f"[{current_time}] [DRAMAS_BOT] [{status_type}] {message}\n")
    except Exception:
        pass

def send_error_email(error_msg):
    if not GMAIL_APP_PASSWORD:
        return
    try:
        msg = MIMEText(f"Trendify Dramas Bot Error:\n\n{error_msg}")
        msg['Subject'] = '⚠️ Trendify Dramas Alert'
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
    bot_name = "DRAMAS" # ⚠️ Har bot mein isay change karein (e.g., "HEALTH", "HISTORY", "DRAMAS")
    
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
# MODULE B: DRAMA REVIEW STYLE AI CONTENT
# ==========================================
def generate_ai_article(title, raw_text, original_link):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("API key missing!")

    prompt = f"""
    You are an expert TV critic specializing in global series (Netflix, Turkish, Hollywood, Bollywood). Write a thrilling 400-word article based on this news:
    Topic: {title}\nDetails: {raw_text}\n
    Requirements:
    1. Tone: Exciting and engaging for hardcore fans.
    2. Format entirely in clean HTML (no ```html, no <html> or <body>). 
    3. Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> for headers and <ul> for key takeaways.
    4. At the exact end of the article, add this HTML line for the source link:
    <p style="margin-top: 30px;"><strong>🔗 Official Source & Full Details:</strong> <a href="{original_link}" target="_blank" style="color: #00ffcc;">Click Here to Read More</a></p>
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
# MODULE C & D: BUILD HTML & FRONTEND
# ==========================================
def build_html_page(title, image_url, ai_content):
    safe_title = "".join(x for x in title if x.isalnum() or x.isspace())
    file_name = safe_title.lower().replace(" ", "-") + ".html"
    current_time = datetime.now().strftime("%B %d, %Y")
    
    dramas_folder = "dramas"
    if not os.path.exists(dramas_folder):
        os.makedirs(dramas_folder)
        
    file_path = os.path.join(dramas_folder, file_name)
    
    with open("article_template.html", "r", encoding="utf-8") as f:
        html_template = f.read()
        
    final_html = html_template.replace("{{TITLE}}", title).replace("{{IMAGE_URL}}", image_url).replace("{{CURRENT_TIME}}", current_time).replace("{{AI_CONTENT}}", ai_content)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(final_html)
        
    return file_name

def update_main_pages(title, image_url, file_name, raw_text):
    clean_text = re.sub(r'<[^>]+>', '', raw_text).strip()
    hook_text = clean_text[:120] + "..." if len(clean_text) > 120 else clean_text
    
    new_card_html = f"""<!-- NEW_CARD_HERE -->
        <div class="news-card">
            <img src="{image_url}" alt="Drama Image">
            <h3>{title}</h3>
            <p>{hook_text}</p>
            <a href="dramas/{file_name}" class="read-more">Read Full Breakdown</a>
        </div>"""
        
    page = "dramas.html"
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
    print("🔥 DRAMAS BOT RUNNING...\n")
    try:
        drama_news = scrape_unposted_dramas()
        if drama_news:
            print(f"🤖 Generating Drama Article: {drama_news['title']}")
            # Notice we are now passing the original_link
            article = generate_ai_article(drama_news["title"], drama_news["raw_text"], drama_news["original_link"])
            file_name = build_html_page(drama_news["title"], drama_news["image_url"], article)
            
            if file_name:
                update_main_pages(drama_news["title"], drama_news["image_url"], file_name, drama_news["raw_text"])
                add_log("SUCCESS", f"Drama Post Published: {drama_news['title']}")
                update_rss(drama_news["title"], file_name, drama_news["image_url"])
                send_telegram_message(drama_news["title"])
                print("🎉 SUCCESS! Nayi Drama post ho chuki hai.")
        else:
            print("⏳ Koi nayi drama update nahi mili.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        send_error_email(error_details)

# ==========================================
# 🚀 PIPELINE RUNNER (DRAMAS)
# ==========================================
def run_single_pipeline():
    print("🔥 DRAMAS BOT RUNNING...\n")
    try:
        drama = scrape_unposted_dramas()
        if drama:
            print(f"🤖 Generating Drama Post: {drama['title']}")
            article = generate_ai_article(drama["title"], drama["raw_text"], drama["original_link"])
            file_name = build_html_page(drama["title"], drama["image_url"], article)
            
            if file_name:
                update_main_pages(drama["title"], drama["image_url"], file_name, drama["raw_text"])
                add_log("SUCCESS", f"Drama Published: {drama['title']}")
                update_dashboard("SUCCESS", f"Published: {drama['title']}")
                update_rss(drama["title"], file_name, drama["image_url"])
                send_telegram_message(drama["title"])
                print("🎉 SUCCESS! Nayi Drama post ho chuki hai.")
        else:
            print("⏳ Koi naya drama update nahi mila.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        update_dashboard("ERROR", error_details)
        send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()
