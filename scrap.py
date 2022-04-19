"""
send email with today most rating article from habr

create file email.ini from template email-example.ini
"""

import datetime
import os
import smtplib
import sys
from configparser import ConfigParser
import email.message

import requests
from bs4 import BeautifulSoup

BODY_TEMPLATE = """\
- [ ] {voting} [{text}]({url})\
"""


def get_habr_articles(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    articles = soup.find_all("article", class_="tm-articles-list__item")
    for article in articles:
        link = article.find("a", class_="tm-article-snippet__title-link")
        if not link:
            continue
        voting = article.find("span", class_="tm-votes-meter__value")
        url = "https://habr.com" + link.get("href")
        yield dict(text=link.text, voting=voting.text, url=url)


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


def main():
    current = datetime.datetime.now()
    current_date = current.strftime("%Y-%m-%d")

    if "weekly" in sys.argv:
        subject = f"New weekly HABR articles {current_date}"
        urls = [
            "https://habr.com/ru/top/weekly/",
            "https://habr.com/ru/top/weekly/page2/",
            "https://habr.com/ru/top/weekly/page3/",
        ]
    else:
        subject = f"New HABR articles {current_date}"
        urls = ["https://habr.com/ru/top/daily/"]

    texts = [
        BODY_TEMPLATE.format(**article)
        for url in urls
        for article in get_habr_articles(url)
    ]
    body = "\n".join(texts)

    if "print" in sys.argv:
        print(subject)
        print(body)
    else:
        send_email(subject, body)


if __name__ == "__main__":
    main()
