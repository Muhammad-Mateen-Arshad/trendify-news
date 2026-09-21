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
# 50 PAKISTAN JOBS RSS FEEDS (Govt & Private)
# ==========================================
JOB_FEEDS = [
    "https://news.google.com/rss/search?q=government+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=private+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=fpsc+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=ppsc+jobs+lahore&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=spsc+jobs+sindh&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=kppsc+jobs+peshawar&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=bpsc+jobs+balochistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=pakistan+army+jobs&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=pakistan+navy+jobs&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=pakistan+air+force+jobs&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=wapda+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=railway+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=nadra+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=fia+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=asf+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=fbr+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=police+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=teaching+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=lecturer+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=banking+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=state+bank+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=national+bank+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=hospital+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=medical+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=engineering+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=software+engineering+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=it+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=data+entry+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=marketing+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=sales+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=hr+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=accounting+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=finance+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=ngo+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=un+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=part+time+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=remote+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=freelance+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=internship+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=management+trainee+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=driver+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=security+guard+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=customs+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=airport+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=pia+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=ptcl+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=ogdcl+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=sui+gas+jobs+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=karachi+jobs&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=islamabad+jobs&hl=en-PK&gl=PK&ceid=PK:en",
    
    # --- 50 INTERNATIONAL & REMOTE JOBS ---
    "https://news.google.com/rss/search?q=remote+software+engineer+jobs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+marketing+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+data+analyst+jobs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=work+from+home+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+customer+support+jobs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+project+manager+jobs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+graphic+design+jobs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+accounting+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+sales+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+hr+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=jobs+in+usa+visa+sponsorship&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=tech+jobs+silicon+valley&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=cybersecurity+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=healthcare+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=nursing+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=finance+jobs+new+york&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=engineering+jobs+texas&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=ai+machine+learning+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=amazon+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=google+apple+jobs+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=jobs+in+london+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=tier+2+visa+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=nhs+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=software+developer+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=marketing+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=finance+jobs+london&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=remote+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=engineering+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=care+worker+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=accountant+jobs+uk&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=jobs+in+toronto+canada&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=lmia+jobs+canada&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=tech+jobs+vancouver&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=remote+jobs+canada&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=nursing+jobs+canada&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=truck+driver+jobs+canada&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=engineering+jobs+canada&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=finance+jobs+canada&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=jobs+in+sydney+australia&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=visa+sponsorship+jobs+australia&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=mining+jobs+australia&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=tech+jobs+australia&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=healthcare+jobs+australia&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=remote+jobs+australia&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=jobs+in+dubai+uae&hl=en-AE&gl=AE&ceid=AE:en",
    "https://news.google.com/rss/search?q=tech+jobs+dubai&hl=en-AE&gl=AE&ceid=AE:en",
    "https://news.google.com/rss/search?q=jobs+in+saudi+arabia+riyadh&hl=en-SA&gl=SA&ceid=SA:en",
    "https://news.google.com/rss/search?q=remote+crypto+web3+jobs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=remote+content+writing+jobs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=freelance+upwork+fiverr+jobs&hl=en-US&gl=US&ceid=US:en"
]

# ==========================================
# MODULE: RSS FEED (JOBS ONLY)
# ==========================================
def update_rss(title, file_name, image_url):
    website_url = f"https://Muhammad-Mateen-Arshad.github.io/trendify-news/jobs/{file_name}"
    post_caption = f"💼 New Job Alert in Pakistan: {title} \n\n👇 Apply and read full details here:\n{website_url}"
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify Portal - Pakistan Jobs</title>
  <link>https://Muhammad-Mateen-Arshad.github.io/trendify-news/</link>
  <description>Latest Government and Private Jobs in Pakistan</description>
  <item>
    <title>{title}</title>
    <description>{post_caption}</description>
    <link>{website_url}</link>
    <pubDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>
    <enclosure url="{image_url}" type="image/jpeg" length="0" />
  </item>
</channel>
</rss>"""

    with open("rss_jobs.xml", "w", encoding="utf-8") as f:
        f.write(rss_content)
    print("✅ Dedicated RSS Feed Updated: rss_jobs.xml")

def send_telegram_message(title):
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        return
    
    channel_id = "@trendify_news_live"
    website_url = "https://Muhammad-Mateen-Arshad.github.io/trendify-news/jobs.html"
    message = f"💼 *NEW JOB OPPORTUNITY IN PAKISTAN* 💼\n\n📌 {title}\n\n👇 Check details & apply now:\n{website_url}"
    
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
    log_entry = f"[{current_time}] [JOBS_BOT] [{status_type}] {message}\n"
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

def send_error_email(error_msg):
    if not GMAIL_APP_PASSWORD:
        return
    try:
        msg = MIMEText(f"Trendify Jobs Bot Error:\n\n{error_msg}")
        msg['Subject'] = '⚠️ Trendify Jobs Alert - Execution Error'
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
def scrape_unposted_jobs():
    if not os.path.exists("posted_jobs.txt"):
        open("posted_jobs.txt", "w", encoding="utf-8").close()
        
    with open("posted_jobs.txt", "r", encoding="utf-8") as f:
        posted_history = f.read().splitlines()

    shuffled_feeds = JOB_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    for feed_url in shuffled_feeds:
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_jobs.txt", "a", encoding="utf-8") as f:
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
                        encoded_prompt = urllib.parse.quote(entry.title + " corporate office interview professional workplace realistic photography")
                        real_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true&seed={random.randint(1,1000)}"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": real_image_url,
                        "original_link": getattr(entry, 'link', 'https://www.google.com/search?q=jobs+in+pakistan')
                    }
        except Exception as e:
            continue
    return None

# ==========================================
# MODULE B: REAL AI CONTENT
# ==========================================
# ==========================================
# MODULE B: REAL AI CONTENT (WITH BUTTON)
# ==========================================
def generate_ai_article(title, raw_text, original_link):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("API key missing!")

    prompt = f"""
    You are an expert global career consultant. Write a highly engaging, 300-400 word job alert post based on this listing:
    Job Title: {title}\nDetails: {raw_text}\n
    Requirements: Format entirely in clean HTML (no ```html, no <html> or <body>). 
    Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> for headings (like 'Role Overview', 'Eligibility Criteria', 'Why Join?') and <ul> for bullet points.
    Make it sound encouraging for global and local job seekers.
    At the exact end of the article, add this exact HTML button block for the apply link:
    
    <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
        <a href="{original_link}" target="_blank" style="background-color: #00ffcc; color: #111; padding: 15px 30px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: 0.3s;">
            💼 Click Here to Apply (Official Website)
        </a>
    </div>
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
    
    jobs_folder = "jobs"
    if not os.path.exists(jobs_folder):
        os.makedirs(jobs_folder)
        
    file_path = os.path.join(jobs_folder, file_name)
    
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
            <img src="{image_url}" alt="Job Image">
            <h3>{title}</h3>
            <p>{hook_text}</p>
            <a href="jobs/{file_name}" class="read-more">View Job Details</a>
        </div>"""
        
    page = "jobs.html"
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
    print("🔥 JOBS BOT RUNNING...\n")
    try:
        job = scrape_unposted_jobs()
        if job:
            print(f"🤖 Generating Job Post: {job['title']}")
            article = generate_ai_article(job["title"], job["raw_text"], job["original_link"])
            file_name = build_html_page(job["title"], job["image_url"], article)
            
            if file_name:
                update_main_pages(job["title"], job["image_url"], file_name, job["raw_text"])
                add_log("SUCCESS", f"Job Published: {job['title']}")
                update_rss(job["title"], file_name, job["image_url"])
                send_telegram_message(job["title"])
                print("🎉 SUCCESS! Nayi Job post ho chuki hai.")
        else:
            print("⏳ Koi nayi job nahi mili.")
    except Exception as e:
        error_details = str(e)
        add_log("ERROR", error_details)
        send_error_email(error_details)

if __name__ == "__main__":
    run_single_pipeline()