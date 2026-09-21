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
DRAMA_FEEDS = [
    # Netflix & Streaming
    "https://netflixlife.com/feed/", "https://www.whats-on-netflix.com/feed/", "https://decider.com/feed/", 
    "https://tvline.com/category/streaming/feed/", "https://vaguevisages.com/feed/",
    # Turkish & Global Historical (Mehmed, Ertugrul, etc.)
   # Turkish Historical & Romantic Dramas
    "https://dizilah.com/feed",
    "https://turkishtvclub.com/feed/",
    "https://www.teammy.com/feed/",
    "https://geekycraze.com/category/entertainment/turkish-dramas/feed/",
    "https://www.dailysabah.com/arts/rss",
    "https://www.hurriyetdailynews.com/rss/arts",
    "https://www.trtworld.com/arts-and-culture/rss.xml",
    "https://www.albawaba.com/rss/entertainment",
    "https://en.qantara.de/taxonomy/term/3257/all/feed",
    "https://arabamericannews.com/category/arts-and-entertainment/feed/",
    # Hollywood & Western TV
    "https://deadline.com/v/tv/feed/", "https://variety.com/v/tv/feed/", "https://www.hollywoodreporter.com/c/tv/tv-news/feed/",
    "https://www.cinemablend.com/television/rss.xml", "https://tvline.com/feed/", "https://collider.com/feed/",
    "https://screenrant.com/feed/tv/", "https://ew.com/feed/", "https://www.empireonline.com/tv/news/rss",
    "https://www.slashfilm.com/feed/", "https://www.thewrap.com/category/tv/feed/", "https://www.indiewire.com/c/tv/feed/",
    "https://www.ign.com/feed/tv", "https://comicbook.com/tv-shows/feed/", "https://bleedingcool.com/tv/feed/",
    "https://www.tvinsider.com/feed/", "https://www.denofgeek.com/tv/feed/", "https://www.digitalspy.com/tv/rss/",
    "https://www.spoilertv.com/feeds/posts/default", "https://telltaletv.com/feed/",
    # Bollywood & Indian TV
    "https://www.bollywoodhungama.com/rss/news.xml", "https://www.pinkvilla.com/feed/entertainment.xml", 
    "https://c.ndtv.com/ndtv/feeds/entertainment.xml", "https://indianexpress.com/section/entertainment/feed/",
    "https://www.hindustantimes.com/feeds/rss/entertainment/rssfeed.xml", "https://zeenews.india.com/rss/entertainment-news.xml",
    "https://www.news18.com/rss/entertainment.xml", "https://www.firstpost.com/rss/entertainment.xml",
    "https://www.mid-day.com/Resources/midday/rss/entertainment-news.xml", "https://www.dnaindia.com/feeds/entertainment.xml",
    # Tollywood & South Indian
    "https://www.123telugu.com/feed", "https://www.gulte.com/feed", "https://tracktollywood.com/feed/",
    "https://telugucinema.com/feed", "https://www.greatandhra.com/rss.xml", "https://www.mirchi9.com/feed/",
    "https://www.cinejosh.com/rss/news", "https://www.tollywood.net/feed/", "https://www.indiaherald.com/rss/tollywood",
    "https://www.behindwoods.com/rss/tamil-movies-news.xml"
]


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


# ==========================================
# MODULE A: SCRAPER & IMAGE
# ==========================================
def scrape_unposted_dramas():
    if not os.path.exists("posted_dramas.txt"):
        open("posted_dramas.txt", "w", encoding="utf-8").close()
        
    with open("posted_dramas.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    shuffled_feeds = DRAMA_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    for feed_url in shuffled_feeds:
        try:
            response = requests.get(feed_url, timeout=15)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_dramas.txt", "a", encoding="utf-8") as f:
                        f.write(entry.title + "\n")
                    
                    # Real Image Logic
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
                    
                    if not real_image_url:
                        encoded_prompt = urllib.parse.quote(entry.title + " tv series drama realistic cinematic scene high quality")
                        real_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": real_image_url,
                        "original_link": getattr(entry, 'link', 'https://netflix.com')
                    }
        except Exception:
            continue
    return None

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
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(GEMINI_API_KEYS)
                client = genai.Client(api_key=GEMINI_API_KEYS[CURRENT_KEY_INDEX])
                time.sleep(2)
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

if __name__ == "__main__":
    run_single_pipeline()