import smtplib
from email.mime.text import MIMEText

# Yahan apni asal details daalein
GMAIL_SENDER = "mateenarshad877@gmail.com" 
GMAIL_APP_PASSWORD = "yqhiqgssbfflkjgb" 
GMAIL_RECEIVER = "mateenarshad877@gmail.com"

print("⏳ Email bhejne ki koshish kar raha hoon...")

try:
    msg = MIMEText("Mateen Bhai! Agar yeh email mil gayi hai, toh system bilkul theek hai!")
    msg['Subject'] = '✅ Trendify SMTP Test'
    msg['From'] = GMAIL_SENDER
    msg['To'] = GMAIL_RECEIVER

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
    server.sendmail(GMAIL_SENDER, GMAIL_RECEIVER, msg.as_string())
    server.quit()
    print("🎉 SUCCESS! Email chali gayi hai. Apna inbox check karein!")
    
except Exception as e:
    print(f"❌ ERROR AAYA HAI:\n{e}")