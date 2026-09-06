import os
import smtplib
import ssl
from email.mime.text import MIMEText


def send_digest_email(body: str, subject: str) -> None:
    """Sends via Gmail SMTP using an App Password (not your regular Gmail
    password — see SETUP.md). Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD
    env vars; EMAIL_TO defaults to GMAIL_ADDRESS itself."""
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    to_addr = os.environ.get("EMAIL_TO", sender)

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_addr

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, [to_addr], msg.as_string())
