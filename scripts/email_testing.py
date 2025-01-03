import os
import smtplib
from email.mime.text import MIMEText

def sendEmail(subject, message):
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    address = os.environ.get('EMAIL')
    password = os.environ.get('PASSWORD')

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = address
    msg['To'] = address

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(address, password)
            server.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

#sendEmail("This is a drill", "Hello, World!")
