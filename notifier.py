import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load global credentials
load_dotenv(os.path.expanduser("~/.openclaw/.env"))

def send_alert_email(subject, body):
    sender_email = "woodwater2026@gmail.com"
    receiver_email = "woodwater2026@gmail.com" # Default to self for alerts
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not password:
        print("[ERROR] GMAIL_APP_PASSWORD not found in environment.")
        return False

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"[SUCCESS] Alert email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

if __name__ == "__main__":
    # Test alert
    send_alert_email("Test Alert from Water Woods", "This is a test notification from your AI partner.")
