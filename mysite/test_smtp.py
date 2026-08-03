import smtplib
from email.mime.text import MIMEText

# Gmail SMTP settings
smtp_server = "smtp.gmail.com"
smtp_port = 587
username = "rmfpbistrackdata@gmail.com"       # replace with your Gmail
password = "sshk qjnl osku hayy"           # replace with 16-char app password

# Build the email
msg = MIMEText("This is a test email sent from Python using Gmail + App Password.")
msg["Subject"] = "Gmail SMTP Test"
msg["From"] = username
msg["To"] = "chill@rmfp.com"                  # replace with your target recipient

# Send the email
try:
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()                     # upgrade the connection to secure TLS
        server.login(username, password)
        server.sendmail(username, ["chill@rmfp.com"], msg.as_string())
    print("✅ Test email sent successfully!")
except Exception as e:
    print("❌ Error:", e)
