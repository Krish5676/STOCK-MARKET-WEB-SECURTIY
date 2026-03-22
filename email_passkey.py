import smtplib
import random
from email.mime.text import MIMEText

SENDER_EMAIL = "kvp31102007@gmail.com"
APP_PASSWORD = "yhvq kzjh bapv cvxu"

def send_passkey(receiver_email):
    passkey = str(random.randint(100000, 999999))

    msg = MIMEText(f"Your Trade Passkey is: {passkey}")
    msg['Subject'] = "Trade Verification Passkey"
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.send_message(msg)
    server.quit()

    return passkey