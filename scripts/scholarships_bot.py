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
# 50+ SCHOLARSHIPS & OPPORTUNITIES FEEDS
# ==========================================
SCHOLARSHIP_FEEDS = [
    # Dedicated Scholarship Portals
    "https://www.scholars4dev.com/feed/",
    "https://opportunitydesk.org/feed/",
    "https://youthop.com/feed/",
    
    # Fully Funded Global
    "https://news.google.com/rss/search?q=fully+funded+scholarships+for+international+students&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=bachelors+scholarship+fully+funded&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=masters+scholarship+fully+funded&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=phd+scholarship+fully+funded&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=postdoc+fellowship+fully+funded&hl=en-US&gl=US&ceid=US:en",
    
    # Pakistan Specific Opportunities
    "https://news.google.com/rss/search?q=scholarships+for+pakistani+students&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=hec+scholarships+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=us+fp+fulbright+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=peef+scholarships+punjab&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=ehsaas+undergraduate+scholarship&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=need+based+scholarship+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    "https://news.google.com/rss/search?q=merit+scholarship+pakistan&hl=en-PK&gl=PK&ceid=PK:en",
    
    # Top International Scholarships
    "https://news.google.com/rss/search?q=chevening+scholarship+uk&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=erasmus+mundus+scholarship&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=fulbright+scholarship+usa&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=daad+scholarship+germany&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=mext+scholarship+japan&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=eiffel+excellence+scholarship+france&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=gates+cambridge+scholarship&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=rhodes+scholarship+oxford&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=knight-hennessy+scholars+stanford&hl=en-US&gl=US&ceid=US:en",
    
    # Country Specific Scholarships
    "https://news.google.com/rss/search?q=study+in+usa+scholarships&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=study+in+uk+scholarships&hl=en-GB&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=study+in+canada+scholarships&hl=en-CA&gl=CA&ceid=CA:en",
    "https://news.google.com/rss/search?q=study+in+australia+scholarships&hl=en-AU&gl=AU&ceid=AU:en",
    "https://news.google.com/rss/search?q=study+in+germany+scholarships&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=study+in+china+csc+scholarship&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=study+in+italy+scholarships&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=study+in+south+korea+kgsp&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=study+in+turkey+turkiye+burslari&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=study+in+saudi+arabia+scholarships&hl=en-US&gl=US&ceid=US:en",
    
    # Partial Funding & Financial Aid
    "https://news.google.com/rss/search?q=partial+scholarship+international+students&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=tuition+fee+waiver+scholarship&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=financial+aid+international+students&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=university+grants+international+students&hl=en-US&gl=US&ceid=US:en",
    
    # Fellowships & Internships
    "https://news.google.com/rss/search?q=international+fellowship+programs&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=fully+funded+summer+internships&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=un+internships+fully+funded&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=cern+summer+student+program&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=world+bank+internship&hl=en-US&gl=US&ceid=US:en",
    
    # Subject Specific
    "https://news.google.com/rss/search?q=stem+scholarships+international+students&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=medical+scholarships+international+students&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=engineering+scholarships+international+students&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=arts+humanities+scholarships&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=women+in+tech+scholarships&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=mba+scholarships+international&hl=en-US&gl=US&ceid=US:en"
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
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    for feed_url in shuffled_feeds:
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                if entry.title not in posted_history:
                    with open("posted_scholarships.txt", "a", encoding="utf-8") as f:
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
                        image_prompt = entry.title + " university campus students studying library high quality realistic"
                        encoded_prompt = urllib.parse.quote(image_prompt)
                        real_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true&seed={random.randint(1,1000)}"
                    
                    return {
                        "title": entry.title,
                        "raw_text": getattr(entry, 'summary', entry.title),
                        "image_url": real_image_url,
                        "source_link": getattr(entry, 'link', 'https://www.google.com/search?q=scholarships') 
                    }
        except Exception:
            continue
    return None

# ==========================================
# MODULE B: EDUCATION COUNSELOR AI CONTENT
# ==========================================
def generate_ai_article(title, raw_text, source_link):
    global CURRENT_KEY_INDEX, client
    
    if not GEMINI_API_KEYS:
        raise Exception("API key missing!")

    prompt = f"""
    You are an expert international education counselor. Write a highly informative, encouraging 300-400 word guide based on this scholarship opportunity:
    Opportunity: {title}\nDetails: {raw_text}\n
    Requirements:
    1. Tone: Professional, motivating, and clear for both Pakistani and International students.
    2. Format entirely in clean HTML (no ```html, no <html> or <body>). 
    3. Clearly highlight if it's fully or partially funded.
    4. Use <p>, <h3 style="color: #00ffcc; margin-top: 25px;"> for headings (e.g., 'What is Included', 'Eligibility Criteria') and <ul> for lists.
    5. At the exact end of the article, add this exact HTML button block for the apply link:
    
    <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
        <a href="{source_link}" target="_blank" style="background-color: #FFD700; color: #111; padding: 15px 30px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: 0.3s; text-transform: uppercase;">
            🎓 Click Here to Apply (Official Website)
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
            
            # Module B se article aur button generate hoga
            article = generate_ai_article(schol_news["title"], schol_news["raw_text"], schol_news["source_link"])
            
            file_name = build_html_page(schol_news["title"], schol_news["image_url"], article)
            
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