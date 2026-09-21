import os
import re
from datetime import datetime

SITE_URL = "https://muhammad-mateen-arshad.github.io/trendify-news"
categories = ['news', 'jobs', 'health', 'history', 'dramas', 'scholarships']

master_items = ""
instagram_items = ""

for category in categories:
    cat_items = ""
    if os.path.exists(category):
        for file in os.listdir(category):
            if file.endswith('.html'):
                file_path = os.path.join(category, file)
                link = f"{SITE_URL}/{category}/{file}"
                title = file.replace('-', ' ').replace('.html', '').title()
                
                # HTML file se image nikalne ka logic
                try:
                    with open(file_path, "r", encoding="utf-8") as html_file:
                        html_content = html_file.read()
                    img_match = re.search(r'<img[^>]+src="([^">]+)"', html_content)
                    image_url = img_match.group(1) if img_match else "https://via.placeholder.com/800x400?text=No+Image"
                except:
                    image_url = "https://via.placeholder.com/800x400?text=Error"

                # Normal Item (Master & Category ke liye)
                item_xml = f"""
  <item>
    <title>{title}</title>
    <link>{link}</link>
    <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
  </item>"""
                cat_items += item_xml
                master_items += item_xml

                # Instagram Specific Item (Image + Description ke sath)
                insta_desc = f"{title}. Click on it to see the full details: {link}"
                insta_item_xml = f"""
  <item>
    <title>{title}</title>
    <description>{insta_desc}</description>
    <link>{link}</link>
    <enclosure url="{image_url}" type="image/jpeg" length="0" />
    <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
  </item>"""
                instagram_items += insta_item_xml
    
    # Category RSS
    cat_rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify {category.capitalize()}</title>
  <link>{SITE_URL}/{category}</link>
  <description>Latest {category} updates.</description>
{cat_items}
</channel>
</rss>
"""
    with open(f"rss_{category}.xml", "w", encoding="utf-8") as f:
        f.write(cat_rss_content)

# Master RSS
master_rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify News Mega Portal</title>
  <link>{SITE_URL}</link>
  <description>Latest updates from all categories.</description>
{master_items}
</channel>
</rss>
"""
with open("rss.xml", "w", encoding="utf-8") as f:
    f.write(master_rss_content)

# Instagram RSS
insta_rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Trendify Instagram Feed</title>
  <link>{SITE_URL}</link>
  <description>Latest updates with images for Instagram.</description>
{instagram_items}
</channel>
</rss>
"""
with open("rss_instagram.xml", "w", encoding="utf-8") as f:
    f.write(insta_rss_content)

print("✅ Master, Category, aur Instagram (with images) RSS feeds successfully ban gayi hain!")