import os
from datetime import datetime

SITE_URL = "https://muhammad-mateen-arshad.github.io/trendify-news"
categories = ['news', 'jobs', 'health', 'history', 'dramas', 'scholarships']

# Master RSS ke liye empty string
master_items = ""

for category in categories:
    cat_items = ""
    if os.path.exists(category):
        for file in os.listdir(category):
            if file.endswith('.html'):
                link = f"{SITE_URL}/{category}/{file}"
                title = file.replace('-', ' ').replace('.html', '').title()
                
                item_xml = f"""
  <item>
    <title>{title}</title>
    <link>{link}</link>
    <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
  </item>"""
                # Item ko category aur master dono mein add karein
                cat_items += item_xml
                master_items += item_xml
    
    # Har category ki alag RSS file generate karein
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

# Master RSS file generate karein jisme sab kuch ho
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

print("✅ Master aur saari individual category RSS feeds successfully ban gayi hain!")