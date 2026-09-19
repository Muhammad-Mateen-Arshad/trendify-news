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

# Global Scholarships & Student Opportunities Feeds
SCHOLARSHIP_FEEDS = [
    "https://www.scholars4dev.com/feed/",
    "https://opportunitydesk.org/feed/",
    "https://youthop.com/feed/"
]

# ==========================================
# MODULE: RSS FEED (SCHOLARSHIPS ONLY)
# ==========================================
def update_rss(title, file_name, image_url):
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/scholarships/{file_name}"
    post_caption = f"🎓 Scholarship Alert: {title} \n\n👇 Read full details and apply here:\n{website_url}"
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify Portal - Scholarships</title>
  <link>https://Muhammad-Mateen-Arshad.github.io/trendify-news/</link>
  <description>Fully Funded Scholarships and International Opportunities</description>
  <item>
    <title>{title}</title>
    <description>{post_caption}</description>
    <link>{website_url}</link>
    <pubDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
    <enclosure url="{image_url}" type="image/jpeg" length="0" />
  </item>
</channel>
</rss>"""

    with open("rss_scholarships.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("✅ Dedicated RSS Feed Updated: rss_scholarships.xml")

def send_telegram_message(title):
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return
    
    channel_id = "@trendify_news_live"
    website_url = "https://Muhammad-Mateen-Arshad.github.io/trendify-news/scholarships.html"
    message = f"🎓 *NEW SCHOLARSHIP OPPORTUNITY* 🎓\n\n📌 {title}\n\n👇 Check details & apply:\n{website_url}"
    
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
            f.write(f"[{current_time}] [SCHOLARSHIPS_BOT] [{status_type}] {message}\n")
    except Exception:
        pass

def send_error_email(error_msg):
    if not GMAIL_APP_PASSWORD:
        return
    try:
        msg = MIMEText(f"Trendify Scholarships Bot Error:\n\n{error_msg}")
        msg['Subject'] = '⚠️ Trendify Scholarships Alert'
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
def scrape_unposted_scholarships():
    if not os.path.exists("posted_scholarships.txt"):
        open("posted_scholarships.txt", "w", encoding="utf-8").close()
        
    with open("posted_scholarships.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    shuffled_feeds = SCHOLARSHIP_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    for feed_url in shuffled_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_scholarships.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    image_prompt = entry.title + " international university campus student success graduation high quality realistic"
                    encoded_prompt = urllib.parse.quote(image_prompt)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true&seed={random.randint(1,1000)}"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": image_url,
                        "source_link": entry.link  # 🔥 Original apply link yahan se scrape hoga
                    }
        except Exception:
            continue
    return None

# ==========================================
# MODULE B: EDUCATION COUNSELOR AI CONTENT
# ==========================================
def generate_ai_article(title, raw_text):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("API key missing!")

    prompt = f"""
    You are an expert international education counselor. Write a highly informative, encouraging 300-400 word guide based on this scholarship opportunity:
    Opportunity: {title}\nDetails: {raw_text}\n
    Requirements:
    1. Tone: Professional, motivating, and clear.
    2. Format entirely in clean HTML (no ```html, no <html> or <body>). 
    3. Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> for headings (e.g., 'What is Included', 'Eligibility Criteria', 'How to Apply') and <ul> for lists.
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
    
    scholarships_folder = "scholarships"
    if not os.path.exists(scholarships_folder):
        os.makedirs(scholarships_folder)
        
    file_path = os.path.join(scholarships_folder, file_name)
    
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
            <img src="{image_url}" alt="Scholarship Image">
            <h3>{title}</h3>
            <p>{hook_text}</p>
            <a href="scholarships/{file_name}" class="read-more">View Scholarship Details</a>
        </div>"""
        
    page = "scholarships.html"
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
    print("🔥 SCHOLARSHIPS BOT RUNNING...\n")
    try:
        schol_news = scrape_unposted_scholarships()
        if schol_news:
            print(f"🤖 Generating Scholarship Article: {schol_news['title']}")
            article = generate_ai_article(schol_news["title"], schol_news["raw_text"])
            
            # 🔥 YAHAAN ORIGINAL LINK KA BUTTON ATTACH KIYA GAYA HAI 🔥
            apply_button_html = f"""
            <div style="margin-top: 40px; text-align: center;">
                <a href="{schol_news['source_link']}" target="_blank" style="display: inline-block; padding: 15px 30px; background: #FFD700; color: #000; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 1.2em; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);">
                    Apply / Official Website
                </a>
            </div>
            """
            article_with_button = article + apply_button_html
            
            file_name = build_html_page(schol_news["title"], schol_news["image_url"], article_with_button)
            
            if file_name:
                update_main_pages(schol_news["title"], schol_news["image_url"], file_name, schol_news["raw_text"])
                add_log("SUCCESS", f"Scholarship Post Published: {schol_news['title']}")
                update_rss(schol_news["title"], file_name, schol_news["image_url"])
                send_telegram_message(schol_news["title"])
                print("🎉 SUCCESS! Nayi Scholarship post ho chuki hai.")
        else:
            print("⏳ Koi nayi scholarship nahi mili.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()