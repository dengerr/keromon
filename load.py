import os
import sys
import smtplib
from configparser import ConfigParser
import email.message


def send_email(subject, body):
    # get credentials from config
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "email.ini")
    if os.path.exists(config_path):
        cfg = ConfigParser()
        cfg.read(config_path)
    else:
        print("Config not found! Exiting!")
        sys.exit(1)

    smtp_host = cfg.get("smtp", "host")
    smtp_user = cfg.get("smtp", "user")
    smtp_password = cfg.get("smtp", "password")
    smtp_to = cfg.get("smtp", "to")

    # make email
    msg = email.message.Message()
    msg["From"] = smtp_user
    msg["To"] = smtp_to
    msg["Subject"] = subject
    msg.add_header("Content-Type", "text/plain; charset=UTF-8")
    msg.set_payload(body)

    # send email
    server = smtplib.SMTP_SSL(smtp_host, 465)
    server.ehlo()
    server.login(smtp_user, smtp_password)
    server.sendmail(smtp_user, smtp_to, msg.as_string().encode("utf-8"))
    server.close()
