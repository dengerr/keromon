"""
send email with today most rating article from habr

create file email.ini with text:
[smtp]
smtp_host = smtp.gmail.com
smtp_user = example@gmail.com
smtp_password = Qwer1243!
to = user@example.com, uesr2@example.com
"""

from configparser import ConfigParser
from collections import namedtuple
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import requests
import smtplib

from bs4 import BeautifulSoup


def get_habr_articles():
    url = 'https://habr.com/ru/top/daily/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    articles = soup.find_all('article', class_='tm-articles-list__item')
    for article in articles:
        link = article.find('a', class_='tm-article-snippet__title-link')
        if not link:
            continue
        voting = article.find('span', class_='tm-votes-meter__value')
        url = 'https://habr.com' + link.get('href')
        yield dict(text=link.text, voting=voting.text, url=url)

BODY_TEMPLATE = """\
- [ ] {voting} {text} {url}\
"""

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

    # make emai
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = smtp_to
    part1 = MIMEText(body, "plain", "utf-8")
    msg.attach(part1)

    # send email
    server = smtplib.SMTP_SSL(smtp_host, 465)
    server.ehlo()
    server.login(smtp_user, smtp_password)
    server.sendmail(smtp_user, smtp_to, msg.as_string())
    server.close()


def send_articles():
    articles = get_habr_articles()
    current = datetime.datetime.now()
    subject = 'New HABR articles {}'.format(current.strftime('%Y-%m-%d'))
    texts = [BODY_TEMPLATE.format(**article) for article in articles]
    body = "\n".join(texts)
    send_email(subject, body)


def show_articles():
    articles = get_habr_articles()
    current = datetime.datetime.now()
    texts = [BODY_TEMPLATE.format(**article) for article in articles]
    body = "\n".join(texts)
    print(body)


if __name__ == '__main__':
    #show_articles()
    send_articles()
